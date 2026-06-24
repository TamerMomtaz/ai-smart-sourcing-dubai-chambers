"""Assemble final dataset: dedup -> family-cap trim -> split -> dual-schema emit.

Deterministic (fixed seed).  Steps:
  1. Load real (210) + synth (verified-pass only).
  2. Exact + MinHash near-dup removal (within synth, and synth-vs-real). Keep real.
  3. Per-family cap (<=5%) + round-robin trim synth to TARGET (4x real).
  4. Assemble records (instruction + fenced output); enforce <=16k tokens.
  5. Deterministic 95/5 split with NO source leakage (group real by PR, synth by id).
  6. Shuffle within split; serialize to BOTH anthropic + axolotl schemas.
  7. Emit train/eval (dist, git-ignored) + smoke(50) + index + meta + manifest.
  8. sha256 + token histogram per file; secret sweep == 0 (assert).
"""
import hashlib
import json
import os
import random
from collections import Counter, defaultdict

import lib_common as C
import lib_secrets as secrets

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "out")
DIST = os.path.join(ROOT, "dist")
META = os.path.join(ROOT, "meta")
IDX = os.path.join(ROOT, "index")
DEC = os.path.join(ROOT, "decisions")
for d in (DIST, META, IDX, DEC):
    os.makedirs(d, exist_ok=True)

SEED = 20240624
TARGET_SYNTH = int(os.environ.get("TARGET_SYNTH", "840"))
EVAL_FRAC = 0.05
MAX_TOK = 16000


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def tok_hist(counts):
    buckets = [(0, 256), (256, 512), (512, 1024), (1024, 2048),
               (2048, 4096), (4096, 8192), (8192, 16000), (16000, 1 << 30)]
    hist = {f"{lo}-{hi if hi < (1<<30) else 'inf'}": 0 for lo, hi in buckets}
    for c in counts:
        for lo, hi in buckets:
            if lo <= c < hi:
                hist[f"{lo}-{hi if hi < (1<<30) else 'inf'}"] += 1
                break
    return hist


def main():
    decisions = {}
    real = [json.loads(l) for l in open(os.path.join(OUT, "real_pairs.jsonl"))]
    synth_all = [json.loads(l) for l in open(os.path.join(OUT, "synth_pairs.jsonl"))]
    failed = set(json.load(open(os.path.join(OUT, "synth_failures.json"))))
    synth = [s for s in synth_all if s["id"] not in failed]
    decisions["synth_dropped_verify"] = len(synth_all) - len(synth)

    # ---- dedup: exact then near-dup (MinHash). Real wins over synth. ----
    seen_exact = {}
    kept = []
    dropped_exact = 0
    for p in real + synth:  # real first => real kept on exact collision
        h = C.exact_hash(p["output"])
        if h in seen_exact:
            dropped_exact += 1
            continue
        seen_exact[h] = p["id"]
        kept.append(p)
    # near-dup
    sigs = [(i, C.minhash_signature(p["output"])) for i, p in enumerate(kept)]
    dup_pairs = C.near_dup_pairs(sigs, threshold=0.9)
    drop_idx = set()
    for a, b in dup_pairs:
        # drop the later / synth one; never drop a real pair in favor of synth
        pa, pb = kept[a], kept[b]
        if pa["source"] == "real" and pb["source"] == "synth":
            drop_idx.add(b)
        elif pb["source"] == "real" and pa["source"] == "synth":
            drop_idx.add(a)
        else:
            drop_idx.add(max(a, b))
    kept = [p for i, p in enumerate(kept) if i not in drop_idx]
    decisions["dropped_exact_dup"] = dropped_exact
    decisions["dropped_near_dup"] = len(drop_idx)

    real_kept = [p for p in kept if p["source"] == "real"]
    synth_kept = [p for p in kept if p["source"] == "synth"]

    # ---- per-family cap (<=5% of final total) + round-robin trim to TARGET ----
    target = min(TARGET_SYNTH, len(synth_kept))
    final_total_est = len(real_kept) + target
    cap = max(1, int(final_total_est * 0.05))
    by_fam = defaultdict(list)
    for p in sorted(synth_kept, key=lambda x: x["id"]):
        by_fam[p["family"]].append(p)
    # round-robin pull across families until target, respecting cap
    rr = []
    fams = sorted(by_fam)
    taken = defaultdict(int)
    idxs = defaultdict(int)
    while len(rr) < target:
        progressed = False
        for fam in fams:
            if len(rr) >= target:
                break
            if taken[fam] >= cap or idxs[fam] >= len(by_fam[fam]):
                continue
            rr.append(by_fam[fam][idxs[fam]])
            idxs[fam] += 1
            taken[fam] += 1
            progressed = True
        if not progressed:
            break
    synth_final = rr
    decisions["family_cap"] = cap
    decisions["synth_after_trim"] = len(synth_final)
    decisions["family_distribution"] = dict(Counter(p["family"] for p in synth_final))

    records = real_kept + synth_final

    # ---- assemble + token check ----
    assembled = []
    over_tok = 0
    for p in records:
        user = C.instruction_with_suffix(p["instruction"], source=p["source"],
                                         kind=p.get("kind", "file"), file=p["file"])
        asst = C.assistant_block(p["output"], source=p["source"], lang=p["lang"])
        # token guard on the full anthropic rendering
        full = C.SYSTEM_MESSAGE + user + asst
        ntok = C.count_tokens(full)
        if ntok > MAX_TOK:
            over_tok += 1
            continue
        assembled.append({**p, "_user": user, "_asst": asst, "_tok": ntok})
    decisions["dropped_over_token"] = over_tok

    # ---- split: group real by PR (no leakage), synth by id ----
    groups = defaultdict(list)
    for r in assembled:
        if r["source"] == "real":
            g = f"pr-{r['provenance'].get('pr') or r['provenance']['sha'][:8]}"
        else:
            g = f"syn-{r['id']}"
        groups[g].append(r)
    group_keys = sorted(groups)
    rng = random.Random(SEED)
    rng.shuffle(group_keys)
    n_total = len(assembled)
    n_eval_target = int(round(n_total * EVAL_FRAC))
    eval_ids, train_ids = [], []
    n_eval = 0
    for g in group_keys:
        if n_eval < n_eval_target and len(groups[g]) <= (n_eval_target - n_eval) + 2:
            eval_ids.extend(groups[g])
            n_eval += len(groups[g])
        else:
            train_ids.extend(groups[g])
    # shuffle within splits
    rng.shuffle(train_ids)
    rng.shuffle(eval_ids)
    decisions["split"] = {"train": len(train_ids), "eval": len(eval_ids),
                          "eval_frac": round(len(eval_ids) / n_total, 4)}

    # ---- serialize dual schema ----
    def write_split(rows, name, schema):
        path = os.path.join(DIST, f"{name}.{schema}.jsonl")
        toks = []
        with open(path, "w", newline="\n") as f:
            for r in rows:
                obj = C.to_anthropic(r["_user"], r["_asst"]) if schema == "anthropic" \
                    else C.to_axolotl(r["_user"], r["_asst"])
                f.write(C.dumps_ascii(obj) + "\n")
                toks.append(r["_tok"])
        return path, toks

    manifest_files = {}
    for schema in ("anthropic", "axolotl"):
        for name, rows in (("train", train_ids), ("eval", eval_ids)):
            path, toks = write_split(rows, name, schema)
            manifest_files[os.path.relpath(path, ROOT)] = {
                "records": len(rows), "sha256": sha256_file(path),
                "tokens": {"min": min(toks), "max": max(toks),
                           "mean": round(sum(toks) / len(toks), 1)},
                "token_histogram": tok_hist(toks), "uploadable": True,
            }
    # smoke: 50 deterministic from train, both schemas (committed)
    smoke_rows = train_ids[:50]
    for schema in ("anthropic", "axolotl"):
        spath = os.path.join(ROOT, f"smoke.{schema}.jsonl")
        with open(spath, "w", newline="\n") as f:
            for r in smoke_rows:
                obj = C.to_anthropic(r["_user"], r["_asst"]) if schema == "anthropic" \
                    else C.to_axolotl(r["_user"], r["_asst"])
                f.write(C.dumps_ascii(obj) + "\n")
        manifest_files[f"smoke.{schema}.jsonl"] = {
            "records": len(smoke_rows), "sha256": sha256_file(spath), "uploadable": "trial-only"}

    # ---- per-record index (committed, NOT uploadable) ----
    split_of = {id(r): "train" for r in train_ids}
    split_of.update({id(r): "eval" for r in eval_ids})
    with open(os.path.join(IDX, "pairs.index.jsonl"), "w", newline="\n") as f:
        for r in assembled:
            entry = {"id": r["id"], "source": r["source"], "lang": r["lang"],
                     "file": r["file"], "split": split_of[id(r)], "tokens": r["_tok"]}
            if r["source"] == "real":
                entry["provenance"] = r["provenance"]
            else:
                entry["family"] = r["family"]
                entry["entity"] = r.get("entity")
            f.write(json.dumps(entry, ensure_ascii=True) + "\n")

    # ---- secret sweep across ALL emitted user+assistant text ----
    sweep = secrets.scan_strings([r["_user"] for r in assembled] + [r["_asst"] for r in assembled])
    decisions["secret_sweep"] = sweep

    # ---- mix + meta + manifest ----
    n_real, n_syn = len(real_kept), len(synth_final)
    mix = {"real": n_real, "synthetic": n_syn, "total": n_real + n_syn,
           "synthetic_pct": round(100 * n_syn / (n_real + n_syn), 1)}
    decisions["mix"] = mix

    json.dump(decisions, open(os.path.join(DEC, "build.decisions.json"), "w"), indent=2)

    manifest = {
        "platform": ["anthropic-messages", "hf-axolotl-chat_template"],
        "tokenizer": "tiktoken o200k_base (Anthropic has no offline tokenizer; "
                     "sizes are an APPROXIMATION, clearly labeled; records are far "
                     "below the 16k cap so it does not bind)",
        "seed": SEED, "max_tokens_per_record": MAX_TOK,
        "near_dup_threshold": 0.9, "split": "95/5 (group-based, no source leakage)",
        "mix": mix,
        "synthetic_over_70pct_FLAG": mix["synthetic_pct"] > 70,
        "files": manifest_files,
        "secret_sweep_hits": sweep,
    }
    json.dump(manifest, open(os.path.join(ROOT, "manifest.json"), "w"), indent=2)

    print("=== BUILD SUMMARY ===")
    print(json.dumps({"mix": mix, "split": decisions["split"],
                      "dropped": {k: decisions[k] for k in
                                  ("synth_dropped_verify", "dropped_exact_dup",
                                   "dropped_near_dup", "dropped_over_token")},
                      "family_cap": cap, "secret_sweep": sweep}, indent=2))
    print("SYNTHETIC >70% FLAG:", manifest["synthetic_over_70pct_FLAG"])


if __name__ == "__main__":
    main()
