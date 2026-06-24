"""Split curated real units into batch files for parallel instruction-authoring.

Each batch is a JSON list of units (id, file, lang, kind, part info, seed text,
full diff).  Subagents read one batch, author one grounded instruction per unit,
and write results back.  Deterministic ordering (by id).
"""
import json
import os

OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "out"))
BATCH_DIR = os.environ["BATCH_DIR"]
BATCH_SIZE = int(os.environ.get("BATCH_SIZE", "14"))

units = [json.loads(l) for l in open(os.path.join(OUT, "real_units.curated.jsonl"))]
units.sort(key=lambda u: u["id"])

os.makedirs(BATCH_DIR, exist_ok=True)
n = 0
for i in range(0, len(units), BATCH_SIZE):
    n += 1
    batch = []
    for u in units[i:i + BATCH_SIZE]:
        batch.append({
            "id": u["id"],
            "file": u["file"],
            "lang": u["lang"],
            "kind": u["kind"],
            "part": f"{u['part']+1}/{u['n_parts']}",
            "seed_subject": u["seed_subject"],
            "seed_message": u["seed_message"],
            "diff": u["diff"],
        })
    with open(os.path.join(BATCH_DIR, f"real_batch_{n:02d}.json"), "w") as f:
        json.dump(batch, f, indent=1)
print(f"wrote {n} batches of <= {BATCH_SIZE} into {BATCH_DIR} ({len(units)} units)")
