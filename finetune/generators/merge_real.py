"""Merge authored instructions with curated units -> real_pairs.jsonl.

STRICT: every curated unit id must have exactly one authored instruction; every
authored id must map to a real unit.  Reports missing / orphan / duplicate ids
and instruction-quality warnings so any gaps can be re-authored.
"""
import glob
import json
import os
import re

OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "out"))
BATCH_DIR = os.environ["BATCH_DIR"]

units = {u["id"]: u for u in (json.loads(l) for l in open(os.path.join(OUT, "real_units.curated.jsonl")))}

authored: dict[str, str] = {}
dups: list[str] = []
orphans: list[str] = []
for path in sorted(glob.glob(os.path.join(BATCH_DIR, "real_out_*.json"))):
    try:
        rows = json.load(open(path))
    except Exception as e:
        print(f"!! could not parse {os.path.basename(path)}: {e}")
        continue
    for r in rows:
        rid, instr = r.get("id"), (r.get("instruction") or "").strip()
        if rid not in units:
            orphans.append(f"{rid} ({os.path.basename(path)})")
            continue
        if rid in authored:
            dups.append(rid)
            continue
        authored[rid] = instr

missing = sorted(set(units) - set(authored))

# Quality warnings (soft)
META = re.compile(r"\b(this (commit|PR|diff|change)|in the (commit|PR)|pull request|as shown)\b", re.I)
warns = []
for rid, instr in authored.items():
    f = units[rid]["file"]
    base = os.path.basename(f)
    if "`" not in instr:
        warns.append(f"{rid}: no backtick identifier")
    if base not in instr and f not in instr:
        warns.append(f"{rid}: does not name file ({f})")
    if META.search(instr):
        warns.append(f"{rid}: references commit/PR/diff meta")
    if len(instr) < 25:
        warns.append(f"{rid}: very short ({len(instr)} chars)")

# Emit pairs only for matched ids (deterministic id order)
pairs = []
for rid in sorted(units, key=lambda x: int(x.split("-")[1])):
    if rid not in authored:
        continue
    u = units[rid]
    pairs.append({
        "id": rid, "source": "real", "instruction": authored[rid],
        "file": u["file"], "lang": u["lang"], "kind": u["kind"],
        "part": u["part"], "n_parts": u["n_parts"],
        "output": u["diff"],
        "provenance": {"sha": u["sha"], "parent": u["parent"], "pr": u["pr"],
                       "file": u["file"], "part": u["part"], "redacted": u["redacted"]},
    })
with open(os.path.join(OUT, "real_pairs.jsonl"), "w") as fh:
    for p in pairs:
        fh.write(json.dumps(p, ensure_ascii=True) + "\n")

print(f"curated units : {len(units)}")
print(f"authored ids  : {len(authored)}")
print(f"matched pairs : {len(pairs)}")
print(f"MISSING ({len(missing)}): {missing}")
print(f"DUP ids ({len(dups)}): {dups}")
print(f"ORPHAN ids ({len(orphans)}): {orphans}")
print(f"quality warnings ({len(warns)}):")
for w in warns[:40]:
    print("   -", w)
