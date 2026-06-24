"""Merge synthesis agent outputs -> synth_pairs.jsonl (pre-verify).

Validates cell coverage against the assignments, secret-scans + redacts every
instruction and code body, and reports missing / orphan / duplicate cells.
"""
import glob
import json
import os
import re

import lib_secrets as secrets

OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "out"))
ASSIGN_DIR = os.environ["ASSIGN_DIR"]
SYNTH_DIR = os.environ["SYNTH_DIR"]

# expected cells from assignments
expected = {}
for ap in sorted(glob.glob(os.path.join(ASSIGN_DIR, "assign_*.json"))):
    a = json.load(open(ap))
    fam = a["family"]["key"]
    lang = a["family"]["lang"]
    for c in a["cells"]:
        expected[c["cell_id"]] = {"family": fam, "lang": lang,
                                  "target_file": c["target_file"],
                                  "entity": (c["entity"] or {}).get("name")}

authored, dups, orphans = {}, [], []
for sp in sorted(glob.glob(os.path.join(SYNTH_DIR, "synth_out_*.json"))):
    try:
        rows = json.load(open(sp))
    except Exception as e:
        print(f"!! parse fail {os.path.basename(sp)}: {e}")
        continue
    for r in rows:
        cid = r.get("cell_id")
        if cid not in expected:
            orphans.append(f"{cid} ({os.path.basename(sp)})")
            continue
        if cid in authored:
            dups.append(cid)
            continue
        authored[cid] = r

missing = sorted(set(expected) - set(authored))

redaction_hits = {}
pairs = []
warns = []
for cid in sorted(authored):
    r = authored[cid]
    meta = expected[cid]
    instr = (r.get("instruction") or "").strip()
    code = r.get("code") or ""
    if not instr or not code.strip():
        warns.append(f"{cid}: empty instruction/code")
        continue
    lang = r.get("lang") or meta["lang"]
    file = r.get("file") or meta["target_file"]
    red_instr, h1 = secrets.redact_text(instr)
    red_code, h2 = secrets.redact_text(code)
    for h in h1 + h2:
        k = h.split(":", 1)[0]
        redaction_hits[k] = redaction_hits.get(k, 0) + 1
    if "`" not in red_instr:
        warns.append(f"{cid}: instruction lacks backtick")
    pairs.append({
        "id": cid, "source": "synth", "family": meta["family"],
        "instruction": red_instr, "file": file, "lang": lang,
        "output": red_code, "entity": meta["entity"],
    })

with open(os.path.join(OUT, "synth_pairs.jsonl"), "w") as f:
    for p in pairs:
        f.write(json.dumps(p, ensure_ascii=True) + "\n")

import collections
print(f"expected cells : {len(expected)}")
print(f"authored cells : {len(authored)}")
print(f"emitted pairs  : {len(pairs)}")
print(f"MISSING ({len(missing)}): {missing[:30]}{' ...' if len(missing)>30 else ''}")
print(f"DUP ({len(dups)}): {dups[:20]}")
print(f"ORPHAN ({len(orphans)}): {orphans[:20]}")
print(f"redaction_hits : {redaction_hits}")
print(f"by family: {dict(collections.Counter(p['family'] for p in pairs))}")
print(f"by lang  : {dict(collections.Counter(p['lang'] for p in pairs))}")
print(f"warnings ({len(warns)}): {warns[:25]}")
