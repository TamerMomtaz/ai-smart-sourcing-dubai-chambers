"""Compile-verify synthetic pairs with the repo's OWN toolchain.

Verifies the FULL synth set (stronger than the spec's >=10% sample): Python via
`python -m py_compile` + `ruff check --select E9,F`; JSX/JS via esbuild; SQL via
`sqlfluff parse --dialect postgres`.  Emits per-id pass/fail, the FULL pass-rate,
the deterministic >=10% sample rate, and the list of failing ids to drop/fix.
"""
import json
import os
import random
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor

OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "out"))
ESBUILD = os.environ.get("ESBUILD", "")
SEED = 1337

EXT = {"python": ".py", "jsx": ".jsx", "javascript": ".js", "sql": ".sql"}


def verify_one(pair):
    lang = pair["lang"]
    code = pair["output"]
    ext = EXT.get(lang, ".txt")
    with tempfile.TemporaryDirectory() as t:
        fp = os.path.join(t, "s" + ext)
        with open(fp, "w") as f:
            f.write(code)
        if lang == "python":
            r = subprocess.run(["python3", "-m", "py_compile", fp], capture_output=True, text=True)
            if r.returncode != 0:
                return (pair["id"], lang, False, "py_compile", r.stderr.strip()[-200:])
            r = subprocess.run(["ruff", "check", "--select", "E9,F", "--isolated", fp],
                               capture_output=True, text=True)
            if r.returncode != 0:
                return (pair["id"], lang, False, "ruff", r.stdout.strip()[-200:])
            return (pair["id"], lang, True, "py", "")
        if lang in ("jsx", "javascript"):
            if not ESBUILD:
                return (pair["id"], lang, None, "esbuild-missing", "")
            r = subprocess.run([ESBUILD, fp, "--log-level=error"], capture_output=True, text=True)
            ok = r.returncode == 0
            return (pair["id"], lang, ok, "esbuild", r.stderr.strip()[-200:])
        if lang == "sql":
            r = subprocess.run(["sqlfluff", "parse", "--dialect", "postgres", fp],
                               capture_output=True, text=True)
            bad = r.returncode != 0 or "unparsable" in (r.stdout + r.stderr).lower()
            excerpt = ""
            if bad:
                low = (r.stdout + r.stderr)
                excerpt = low[low.lower().find("unparsable"):][:200] if "unparsable" in low.lower() else (r.stderr or r.stdout)[-200:]
            return (pair["id"], lang, not bad, "sqlfluff", excerpt)
        return (pair["id"], lang, True, "none", "")


def main():
    pairs = [json.loads(l) for l in open(os.path.join(OUT, "synth_pairs.jsonl"))]
    results = []
    with ThreadPoolExecutor(max_workers=12) as ex:
        for res in ex.map(verify_one, pairs):
            results.append(res)

    by_lang = {}
    failures = []
    for pid, lang, ok, tool, err in results:
        d = by_lang.setdefault(lang, {"pass": 0, "fail": 0, "skip": 0})
        if ok is True:
            d["pass"] += 1
        elif ok is False:
            d["fail"] += 1
            failures.append({"id": pid, "lang": lang, "tool": tool, "error": err})
        else:
            d["skip"] += 1

    npass = sum(d["pass"] for d in by_lang.values())
    nfail = sum(d["fail"] for d in by_lang.values())
    full_rate = npass / (npass + nfail) if (npass + nfail) else 1.0

    # deterministic >=10% sample rate
    rng = random.Random(SEED)
    sample = rng.sample(results, max(1, len(results) // 10))
    s_ok = sum(1 for _, _, ok, _, _ in sample if ok is True)
    s_tot = sum(1 for _, _, ok, _, _ in sample if ok is not None)
    sample_rate = s_ok / s_tot if s_tot else 1.0

    report = {"total": len(results), "pass": npass, "fail": nfail,
              "full_pass_rate": round(full_rate, 4),
              "sample_size": len(sample), "sample_pass_rate": round(sample_rate, 4),
              "by_lang": by_lang, "failures": failures}
    with open(os.path.join(OUT, "verify_report.json"), "w") as f:
        json.dump(report, f, indent=2)
    with open(os.path.join(OUT, "synth_failures.json"), "w") as f:
        json.dump([f_["id"] for f_ in failures], f)

    print(f"FULL: {npass}/{npass+nfail} pass = {full_rate*100:.2f}%")
    print(f">=10% SAMPLE: {s_ok}/{s_tot} = {sample_rate*100:.2f}%")
    print("by lang:", json.dumps(by_lang))
    print(f"failures: {len(failures)}")
    for fobj in failures[:25]:
        print(f"  - {fobj['id']} [{fobj['lang']}/{fobj['tool']}] {fobj['error'][:90]}")


if __name__ == "__main__":
    main()
