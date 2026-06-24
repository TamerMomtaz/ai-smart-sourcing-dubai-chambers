"""Curate real units: drop wiring / mount / config-stub fragments.

The spec says: "Drop wiring/import/mount/config-stub fragments rather than
mislabel them."  A per-file diff that ONLY registers a router, adds an import,
appends a nav entry, mounts a <Route/>, or declares a single env-read is not a
meaningful instruction->implementation pair (the real implementation lives in
the route/service/component unit we already captured).  Drop those.

Reads  finetune/out/real_units.jsonl
Writes finetune/out/real_units.curated.jsonl  and appends drop decisions.
"""

from __future__ import annotations

import json
import os
import re

OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "out"))

WIRING_LINE = [
    re.compile(r"^[A-Za-z_][A-Za-z0-9_]*,?$"),                       # bare module name in import tuple
    re.compile(r"^(import |from )\S"),                               # python/js import
    re.compile(r"^import\s+[\w{},*\s]+\s+from\s+['\"]"),             # js default/named import
    re.compile(r"^export\s+(default\s+)?\{?"),                       # export line
    re.compile(r"(include_router|add_middleware|app\.mount|app\.use\(|\.use\(|registerRoute)"),
    re.compile(r"^<Route\b.*/>,?$"),                                 # JSX route mount
    re.compile(r"^\{[^{}]*\b(name|href|label|icon|key|path|element)\b.*\},?$"),  # nav/menu entry
    re.compile(r"^[A-Z][A-Z0-9_]*\s*=\s*_get_env\("),               # config env-read stub
    re.compile(r"^[\)\]\}\(,;:]+$"),                                 # lone punctuation/braces
    re.compile(r"^(#|//|/\*|\*).*"),                                 # comment
    re.compile(r"^$"),                                              # blank
]

WIRING_NET_CAP = 12  # only treat small diffs as wiring


def payload_code(diff: str) -> list[str]:
    out = []
    for ln in diff.split("\n"):
        if ln[:1] in ("+", "-") and ln[:3] not in ("+++", "---"):
            s = ln[1:].strip()
            if s:
                out.append(s)
    return out


def is_wiring(unit: dict) -> str | None:
    if unit["net_lines"] > WIRING_NET_CAP:
        return None
    code = payload_code(unit["diff"])
    if not code:
        return "empty/comment-only"
    if all(any(p.match(c) or p.search(c) for p in WIRING_LINE) for c in code):
        f = unit["file"]
        if f.endswith("main.py"):
            return "route-mount fragment (main.py)"
        if f.endswith("App.jsx"):
            return "route-registration fragment (App.jsx)"
        if "config.py" in f:
            return "config-stub fragment"
        if "Layout" in f:
            return "nav-entry fragment"
        return "wiring/import/mount fragment"
    return None


def main():
    units = [json.loads(l) for l in open(os.path.join(OUT, "real_units.jsonl"))]
    kept, drops = [], []
    for u in units:
        reason = is_wiring(u)
        if reason:
            drops.append({"id": u["id"], "file": u["file"], "net_lines": u["net_lines"], "reason": reason})
        else:
            kept.append(u)
    # renumber kept ids stably (keep original under orig_id for traceability)
    for u in kept:
        u["orig_id"] = u["id"]
    with open(os.path.join(OUT, "real_units.curated.jsonl"), "w") as f:
        for u in kept:
            f.write(json.dumps(u, ensure_ascii=True) + "\n")
    # merge into decisions
    dpath = os.path.join(OUT, "real.decisions.json")
    decisions = json.load(open(dpath))
    decisions.setdefault("curation", {})
    decisions["curation"]["dropped_wiring"] = drops
    decisions["curation"]["kept"] = len(kept)
    json.dump(decisions, open(dpath, "w"), indent=2)

    import collections
    print(f"input units: {len(units)}")
    print(f"dropped wiring/stub: {len(drops)}")
    print(collections.Counter(d["reason"] for d in drops))
    print(f"KEPT (curated real units): {len(kept)}")
    bylang = collections.Counter(u["lang"] for u in kept)
    print("kept by lang:", dict(bylang))


if __name__ == "__main__":
    main()
