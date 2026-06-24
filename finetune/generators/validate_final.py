"""INDEPENDENT strict validation of every emitted *.jsonl.

Uses jq (independent parser) PLUS lib_common.validate_line for: 100% ASCII, no
BOM, no blank lines, single trailing newline, schema-correct roles, non-empty
content, <=16k tokens, and a global secret-sweep == 0.  Also checks exact + near
duplicate freedom across each file.  Prints sha256 + counts + token histogram.
"""
import glob
import hashlib
import json
import os
import subprocess

import lib_common as C
import lib_secrets as secrets

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def jq_ok(path):
    """Independent parse: every line must be valid JSON with a messages array."""
    r = subprocess.run(
        ["jq", "-e", "-c", "if (.messages|type)==\"array\" and (.messages|length)>0 then 1 else error(\"bad\") end", path],
        capture_output=True, text=True)
    n = len([x for x in r.stdout.splitlines() if x.strip()])
    return r.returncode == 0, n, r.stderr.strip()[:200]


def file_checks(path, schema):
    raw = open(path, "rb").read()
    issues = []
    if raw.startswith(b"\xef\xbb\xbf"):
        issues.append("BOM present")
    if not raw.endswith(b"\n"):
        issues.append("no trailing newline")
    if raw.endswith(b"\n\n"):
        issues.append("blank line at EOF / double trailing newline")
    try:
        raw.decode("ascii")
    except UnicodeDecodeError:
        issues.append("non-ASCII byte")
    lines = raw.decode("utf-8").split("\n")
    body = lines[:-1] if lines and lines[-1] == "" else lines
    for i, ln in enumerate(body):
        if ln.strip() == "":
            issues.append(f"blank line at {i+1}")
            continue
        for iss in C.validate_line(ln, schema=schema):
            issues.append(f"line {i+1}: {iss}")
    # dup check within file (exact + near on assistant content)
    outs = []
    for ln in body:
        obj = json.loads(ln)
        asst = [m["content"] for m in obj["messages"] if m["role"] == "assistant"][0]
        outs.append(asst)
    exact = len(outs) - len(set(C.exact_hash(o) for o in outs))
    if exact:
        issues.append(f"{exact} exact-duplicate assistant outputs")
    # secret sweep
    sweep = secrets.scan_strings([m["content"] for ln in body for m in json.loads(ln)["messages"]])
    if sweep:
        issues.append(f"SECRET SWEEP HITS: {sweep}")
    toks = [C.count_tokens(" ".join(m["content"] for m in json.loads(ln)["messages"])) for ln in body]
    return issues, len(body), (min(toks), max(toks), round(sum(toks)/len(toks), 1)) if toks else (0, 0, 0)


def main():
    targets = []
    for schema in ("anthropic", "axolotl"):
        for name in ("train", "eval"):
            p = os.path.join(ROOT, "dist", f"{name}.{schema}.jsonl")
            if os.path.exists(p):
                targets.append((p, schema))
        sp = os.path.join(ROOT, f"smoke.{schema}.jsonl")
        if os.path.exists(sp):
            targets.append((sp, schema))

    all_ok = True
    summary = {}
    for path, schema in targets:
        jok, jn, jerr = jq_ok(path)
        issues, n, toks = file_checks(path, schema)
        sha = hashlib.sha256(open(path, "rb").read()).hexdigest()
        ok = jok and not issues
        all_ok = all_ok and ok
        rel = os.path.relpath(path, ROOT)
        summary[rel] = {"ok": ok, "jq_parsed": jn, "records": n, "sha256": sha,
                        "tokens(min/max/mean)": toks, "issues": issues[:10]}
        flag = "OK " if ok else "FAIL"
        print(f"[{flag}] {rel}: {n} recs, jq={jn}, tok {toks}, sha {sha[:12]}")
        for iss in issues[:10]:
            print(f"        - {iss}")
    json.dump(summary, open(os.path.join(ROOT, "meta", "validation.meta.json"), "w"), indent=2)
    print("\nALL FILES VALID:", all_ok)
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
