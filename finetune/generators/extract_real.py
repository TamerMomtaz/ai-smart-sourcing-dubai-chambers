"""PHASE 1 extractor — real instruction->diff pairs from git history.

Deterministic.  Walks the (shallow) history reachable from a PINNED head commit,
emits one *unit* per (commit, file[, split-part]) after scoping, dropping noise,
size-splitting, secret-redacting, and apply-verifying every emitted diff.

Outputs (to finetune/out/):
  real_units.jsonl        one JSON unit per line (diff + provenance + raw seed)
  real.decisions.json     per-commit / per-file decisions (kept & dropped + why)
  dropped_monsters.json   irreducible hunks / files dropped for size
  pr_map.json             commit-sha -> PR number (from merge commits)

The authored, file-scoped INSTRUCTION is added in a later step; here we capture
the commit/PR seed text only.  Nothing here is uploadable on its own.
"""

from __future__ import annotations

import html
import json
import os
import re
import subprocess
import tempfile
from collections import defaultdict

import lib_secrets as secrets

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "out"))
HEAD = "99bb9ac2cc7f1a89ca357b9e0e14768545343501"  # pinned engineering tip

# ---- size policy (net changed lines) ----
MAX_WHOLE = 150        # <= this: emit the file diff whole
NEW_FILE_WHOLE = 400   # a coherent new file stays whole up to here
HUNK_DROP = 400        # a single irreducible hunk over this is dropped + listed
PACK = 150             # pack hunks / new-file chunks up to ~this many net lines

# ---- path filters: generated / lockfiles / minified / vendored / locale / docs ----
DROP_PATH = [
    (re.compile(r"(^|/)package-lock\.json$"), "lockfile"),
    (re.compile(r"(^|/)(yarn|pnpm)\.lock$"), "lockfile"),
    (re.compile(r"(^|/)(poetry\.lock|Pipfile\.lock)$"), "lockfile"),
    (re.compile(r"\.min\.(js|css)$"), "minified"),
    (re.compile(r"\.map$"), "sourcemap"),
    (re.compile(r"(^|/)(dist|build|node_modules|vendor)/"), "build/vendor output"),
    (re.compile(r"\.generated\.|_pb2\.py$|\.d\.ts$"), "generated"),
    (re.compile(r"(^|/)(locales|i18n)/.*\.json$"), "locale blob"),
    (re.compile(r"\.(png|jpe?g|gif|svg|ico|pdf|woff2?|ttf|eot|xlsx?|docx?|pptx?|zip)$"), "binary/asset"),
    (re.compile(r"\.md$"), "doc-only (markdown)"),
    (re.compile(r"(^|/)\.gitignore$|(^|/)Procfile$|(^|/)\.env"), "config-stub"),
]

# ---- commit-level drops ----
COMMIT_DROP = [
    (re.compile(r"^merge\b", re.I), "merge"),
    (re.compile(r"\b(wip|typo|nit|formatting|whitespace|lint|prettier|reformat)\b", re.I), "wip/typo/style"),
    (re.compile(r"^(bump|chore\(release\)|release v?\d|v\d+\.\d+)", re.I), "version-bump"),
    (re.compile(r"^\W*\w+\W*$"), "one-word"),
]

LANG = {".py": "python", ".jsx": "jsx", ".js": "javascript", ".ts": "typescript",
        ".tsx": "tsx", ".sql": "sql", ".css": "css", ".json": "json", ".toml": "toml",
        ".yml": "yaml", ".yaml": "yaml", ".sh": "bash", ".html": "html"}

FOOTER = re.compile(
    r"^(Co-Authored-By:|Claude-Session:|Signed-off-by:|Generated with|"
    r"🤖|https://claude\.ai/|Closes #|Fixes #|Resolves #).*$",
    re.I,
)


def run_git(args: list[str], check: bool = True) -> str | None:
    r = subprocess.run(["git", "-C", REPO] + args, capture_output=True, text=True)
    if r.returncode != 0:
        if check:
            raise RuntimeError(f"git {' '.join(args)} -> {r.stderr.strip()}")
        return None
    return r.stdout


def lang_of(path: str) -> str:
    _, ext = os.path.splitext(path)
    return LANG.get(ext.lower(), "other")


def path_dropped(path: str) -> str | None:
    for pat, reason in DROP_PATH:
        if pat.search(path):
            return reason
    return None


def commit_dropped(subject: str) -> str | None:
    for pat, reason in COMMIT_DROP:
        if pat.search(subject.strip()):
            return reason
    return None


def clean_message(subject: str, body: str) -> str:
    subject = html.unescape(subject).strip()
    lines = [ln for ln in html.unescape(body).split("\n") if not FOOTER.match(ln.strip())]
    body = "\n".join(lines).strip()
    return (subject + ("\n\n" + body if body else "")).strip()


def build_pr_map() -> dict[str, int]:
    """commit-sha -> PR number, derived from 'Merge pull request #N' commits."""
    out = run_git(["log", HEAD, "--merges", "--format=%H %P|%s"])
    sha2pr: dict[str, int] = {}
    for line in (out or "").splitlines():
        meta, _, subject = line.partition("|")
        m = re.search(r"Merge pull request #(\d+)", subject)
        if not m:
            continue
        pr = int(m.group(1))
        parents = meta.split()[1:]
        if len(parents) < 2:
            continue
        p1, p2 = parents[0], parents[1]
        commits = run_git(["rev-list", f"{p1}..{p2}"], check=False)
        for sha in (commits or "").split():
            sha2pr.setdefault(sha, pr)
    return sha2pr


def parse_file_diff(raw: str):
    """Return (header_lines, [(hunk_header, body_lines, net)], flags)."""
    lines = raw.split("\n")
    header, hunks = [], []
    i, n = 0, len(lines)
    is_new = is_deleted = is_binary = False
    while i < n and not lines[i].startswith("@@"):
        ln = lines[i]
        if ln.startswith("new file"):
            is_new = True
        elif ln.startswith("deleted file"):
            is_deleted = True
        elif ln.startswith("Binary files") or ln.startswith("GIT binary patch"):
            is_binary = True
        header.append(ln)
        i += 1
    while i < n:
        if lines[i].startswith("@@"):
            hh = lines[i]
            body = []
            i += 1
            while i < n and not lines[i].startswith("@@"):
                if lines[i] == "" and i == n - 1:
                    break
                body.append(lines[i])
                i += 1
            net = sum(1 for b in body if b[:1] in ("+", "-"))
            hunks.append((hh, body, net))
        else:
            i += 1
    return header, hunks, {"new": is_new, "deleted": is_deleted, "binary": is_binary}


def emit_modified(header, hunks):
    """Pack hunks of a modified file into sub-diffs ~PACK net lines.

    Returns (subdiffs, dropped_hunks).  A single hunk over HUNK_DROP is dropped.
    """
    subdiffs, dropped = [], []
    cur, cur_net = [], 0
    for hh, body, net in hunks:
        if net > HUNK_DROP:
            dropped.append((hh, net))
            continue
        if cur and cur_net + net > PACK:
            subdiffs.append("\n".join(header + cur))
            cur, cur_net = [], 0
        cur.append(hh)
        cur.extend(body)
        cur_net += net
    if cur:
        subdiffs.append("\n".join(header + cur))
    return subdiffs, dropped


def emit_new_file(path, hunks):
    """Reconstruct a new file as faithful chunked new-file diffs.

    One hunk for a new file (@@ -0,0 +1,N @@).  If small, emit whole; else split
    the added body at blank-line boundaries into ~PACK-line chunks, each a valid
    standalone new-file diff for `path`.
    """
    added = []
    for _, body, _ in hunks:
        added.extend(b[1:] for b in body if b.startswith("+"))
    total = len(added)
    base_header = [f"diff --git a/{path} b/{path}", "new file mode 100644",
                   "--- /dev/null", f"+++ b/{path}"]

    def make(chunk_lines):
        hh = f"@@ -0,0 +1,{len(chunk_lines)} @@"
        body = "\n".join("+" + ln for ln in chunk_lines)
        return "\n".join(base_header + [hh, body])

    if total <= NEW_FILE_WHOLE:
        return [make(added)], total
    # split at blank lines, packing to ~PACK
    chunks, cur = [], []
    for ln in added:
        cur.append(ln)
        if len(cur) >= PACK and ln.strip() == "":
            chunks.append(cur)
            cur = []
    if cur:
        chunks.append(cur)
    # absorb a tiny trailing chunk into the previous one
    if len(chunks) >= 2 and len(chunks[-1]) < 20:
        chunks[-2].extend(chunks[-1])
        chunks.pop()
    return [make(c) for c in chunks], total


def apply_check(parent_sha, path, subdiff, is_new) -> bool:
    with tempfile.TemporaryDirectory() as t:
        if not is_new:
            base = run_git(["show", f"{parent_sha}:{path}"], check=False)
            if base is None:
                return False
            fp = os.path.join(t, path)
            os.makedirs(os.path.dirname(fp) or t, exist_ok=True)
            with open(fp, "w") as f:
                f.write(base)
        patch = os.path.join(t, "p.diff")
        with open(patch, "w") as f:
            f.write(subdiff if subdiff.endswith("\n") else subdiff + "\n")
        r = subprocess.run(["git", "apply", "--check", "p.diff"],
                           cwd=t, capture_output=True, text=True)
        return r.returncode == 0


def main():
    os.makedirs(OUT, exist_ok=True)
    sha2pr = build_pr_map()
    shas = (run_git(["log", HEAD, "--no-merges", "--reverse", "--format=%H"]) or "").split()

    units, decisions, monsters = [], [], []
    counts = defaultdict(int)
    uid = 0
    redaction_hits = defaultdict(int)

    for sha in shas:
        subject = run_git(["show", "-s", "--format=%s", sha]).strip()
        body = run_git(["show", "-s", "--format=%b", sha])
        cdrop = commit_dropped(subject)
        if cdrop:
            decisions.append({"sha": sha, "subject": subject, "action": "drop-commit", "reason": cdrop})
            counts["commit_dropped"] += 1
            continue
        parent = run_git(["rev-parse", f"{sha}^"], check=False)
        if parent is None:
            decisions.append({"sha": sha, "subject": subject, "action": "skip", "reason": "no-parent (shallow boundary)"})
            counts["no_parent"] += 1
            continue
        parent = parent.strip()
        msg = clean_message(subject, body)
        pr = sha2pr.get(sha)

        files = (run_git(["diff", "--name-only", f"{parent}..{sha}"]) or "").split("\n")
        for path in [f for f in files if f.strip()]:
            pdrop = path_dropped(path)
            if pdrop:
                decisions.append({"sha": sha, "file": path, "action": "drop-file", "reason": pdrop})
                counts["file_dropped"] += 1
                continue
            raw = run_git(["diff", f"{parent}..{sha}", "--", path]) or ""
            if not raw.strip():
                continue
            header, hunks, flags = parse_file_diff(raw)
            if flags["binary"]:
                decisions.append({"sha": sha, "file": path, "action": "drop-file", "reason": "binary"})
                counts["file_dropped"] += 1
                continue
            if not hunks:
                continue

            net_total = sum(h[2] for h in hunks)
            if flags["new"]:
                subdiffs, total = emit_new_file(path, hunks)
                kind = "new-file"
                dropped_hunks = []
            elif net_total <= MAX_WHOLE:
                subdiffs = ["\n".join(header + [x for hh, body, _ in hunks for x in [hh] + body])]
                kind = "whole"
                dropped_hunks = []
            else:
                subdiffs, dropped_hunks = emit_modified(header, hunks)
                kind = "split"
            for hh, net in dropped_hunks:
                monsters.append({"sha": sha, "file": path, "hunk": hh, "net_lines": net})
                counts["hunk_dropped_monster"] += 1

            n_parts = len(subdiffs)
            for part_idx, sd in enumerate(subdiffs):
                red, hits = secrets.redact_diff(sd)
                for h in hits:
                    redaction_hits[h.split(":", 1)[0]] += 1
                ok = apply_check(parent, path, red if not hits else sd, flags["new"])
                # If redaction altered context/removed lines, verify pre-redaction
                # (proves the change is real & coherent); emit redacted text.
                applies_preredact = ok if hits else ok
                if not ok and hits:
                    ok = apply_check(parent, path, sd, flags["new"])
                if not ok:
                    decisions.append({"sha": sha, "file": path, "part": part_idx,
                                      "action": "drop-part", "reason": "apply-check failed"})
                    counts["apply_failed"] += 1
                    continue
                uid += 1
                units.append({
                    "id": f"real-{uid:04d}",
                    "sha": sha, "parent": parent, "pr": pr,
                    "file": path, "lang": lang_of(path),
                    "kind": kind, "part": part_idx, "n_parts": n_parts,
                    "net_lines": sum(1 for ln in sd.split("\n") if ln[:1] in ("+", "-") and ln[:3] not in ("+++", "---")),
                    "seed_subject": html.unescape(subject),
                    "seed_message": msg,
                    "redacted": bool(hits),
                    "diff": red if red.endswith("\n") else red + "\n",
                })
                counts["units"] += 1

    with open(os.path.join(OUT, "real_units.jsonl"), "w") as f:
        for u in units:
            f.write(json.dumps(u, ensure_ascii=True) + "\n")
    with open(os.path.join(OUT, "real.decisions.json"), "w") as f:
        json.dump({"counts": dict(counts), "redaction_hits": dict(redaction_hits),
                   "decisions": decisions}, f, indent=2)
    with open(os.path.join(OUT, "dropped_monsters.json"), "w") as f:
        json.dump(monsters, f, indent=2)
    with open(os.path.join(OUT, "pr_map.json"), "w") as f:
        json.dump(sha2pr, f, indent=2)

    print("=== EXTRACTION SUMMARY ===")
    for k in sorted(counts):
        print(f"  {k}: {counts[k]}")
    print(f"  redaction_hits: {dict(redaction_hits)}")
    by_lang = defaultdict(int)
    for u in units:
        by_lang[u["lang"]] += 1
    print(f"  units_by_lang: {dict(by_lang)}")
    print(f"  monsters_dropped: {len(monsters)}")
    print(f"  TOTAL UNITS: {len(units)}")


if __name__ == "__main__":
    main()
