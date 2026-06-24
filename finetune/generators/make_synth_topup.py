"""Top-up assignments to recover dedup losses and reach the 4x (840) target.

Reuses the family specs + entity vocab from make_synth_assignments, but for the
ENTITY-parameterized families only (the 3 generic families have a real variant
ceiling and are left at their unique count).  Fresh entity/axis offsets keep the
new cells distinct from round 1.  Overshoots so build's round-robin trim can hit
exactly 840 while honoring the <=5% per-family cap.
"""
import json
import os

import make_synth_assignments as M

ASSIGN_DIR = os.environ["ASSIGN_DIR"]
PER_FAMILY = int(os.environ.get("TOPUP_PER_FAMILY", "12"))
GENERIC = {"rate_limiter", "retry_decorator", "pytest_logic"}

total = 0
files = 0
for fi, (key, lang, fence, kind, usage, spec, axiskeys) in enumerate(M.FAMILIES):
    if usage == "generic" or key in GENERIC:
        continue  # ceiling reached; do not pad
    cells = []
    for c in range(PER_FAMILY):
        # different strides than round 1 (c*7+fi*3 / axis c+fi) to decorrelate
        ent = M.ENTITIES[(c * 11 + fi * 5 + 13) % len(M.ENTITIES)]
        name, Name, table, fields = ent
        axes = {ak: M.pick(M.A[ak], c + fi + 2) for ak in axiskeys}
        if lang == "sql":
            tf = f"database/{name}_{key.split('_')[-1]}2_migration.sql" if key != "sql_view" else f"database/{name}_view2.sql"
        elif key == "react_list":
            tf = f"frontend/src/pages/{Name}Browser.jsx"
        elif key == "react_form":
            tf = f"frontend/src/components/{Name}Editor.jsx"
        elif key == "react_hook":
            tf = f"frontend/src/hooks/use{Name}Feed.js"
        elif key == "react_dashboard":
            tf = f"frontend/src/pages/{Name}Insights.jsx"
        elif key.startswith("pytest"):
            tf = f"backend/tests/test_{name}_{key.split('_')[-1]}2.py"
        elif key in ("async_route", "webhook_ingest", "rbac_dependency"):
            sub = {"async_route": "routes", "webhook_ingest": "routes", "rbac_dependency": "deps"}[key]
            tf = f"backend/{sub}/{name}_{key}2.py"
        elif key == "background_task":
            tf = f"backend/workers/{name}_worker2.py"
        elif key == "pydantic_model":
            tf = f"backend/models/{name}_models2.py"
        else:
            tf = f"backend/services/{name}_{key}2.py"
        cells.append({
            "cell_id": f"syn-T{fi:02d}-{c:02d}",
            "entity": {"name": name, "Name": Name, "table": table, "fields": fields},
            "axes": axes,
            "target_file": tf,
        })
        total += 1
    payload = {"family": {"key": key, "lang": lang, "fence": fence, "output_kind": kind,
                          "entity_usage": usage, "spec": spec}, "cells": cells}
    with open(os.path.join(ASSIGN_DIR, f"assign_T{fi:02d}_{key}.json"), "w") as f:
        json.dump(payload, f, indent=1)
    files += 1

print(f"wrote {files} top-up family files, {total} new cells into {ASSIGN_DIR}")
