# Fine-tuning dataset — build report

**Target repo:** `tamermomtaz/ai-smart-sourcing-dubai-chambers` (read-only)
**Dev branch:** `claude/cool-meitner-29ymnh`
**Target platforms (dual emit):** Anthropic Messages **and** HF/axolotl (chat_template)
**Date:** 2026-06-24 · **Seed:** 20240624 (deterministic)

> ⚠️ **SYNTHETIC-MAJORITY FLAG:** per your choice of an aggressive ~4× synthesis
> ratio, synthetic pairs are **~80% of the dataset — above the 70% threshold the
> spec says to flag loudly.** This was a deliberate, confirmed decision. The
> real:synthetic mix and exact percentage are in `manifest.json` and below.

---

## 1. What this is

Two-phase, verified instruction→implementation dataset distilled from the repo:

- **Phase 1 (real):** instruction → **unified diff**, extracted from real git
  history (PRs #108–#157), each pair scoped to a single file with an individually
  authored, symbol-grounded instruction.
- **Phase 2 (synthetic):** instruction → **complete file**, authored in the repo's
  exact stack (FastAPI/Supabase/Pydantic v2 · React 18 + Vite/Tailwind `.jsx` ·
  Postgres SQL), extrapolated to advanced patterns (async, retries/backoff,
  idempotency, optimistic concurrency, RLS, observability, migrations, tests) and
  compile-verified with the repo's own toolchain.

Every record carries one consistent system message; the user turn names the single
target file in backticks; the assistant turn is a single fenced code block (a
`diff` for Phase 1, a complete file for Phase 2). Pure ASCII, LF, one trailing
newline, ≤16k tokens/record.

## 2. Sources & method (Phase 1)

- **Range:** shallow clone, pinned HEAD `99bb9ac`; non-merge engineering commits
  PR #108→#157. The initial scaffold predates the clone, so the "drop scaffold"
  rule was moot.
- **Extraction (`extract_real.py`):** per-(commit, file) two-dot diffs
  (`parent..sha`); strip lockfiles/minified/maps/generated/locale/binary/docs;
  drop merges, version-bumps, one-word/wip commits; size-split (≤150 net whole;
  new files to ~400 then chunked at blank-line boundaries; a single irreducible
  hunk >~400 dropped + listed); **every emitted diff verified to apply**
  (`git apply --check` against the reconstructed parent).
- **Curation (`curate_units.py`):** dropped pure wiring/mount/config-stub fragments
  (router mounts in `main.py`, `App.jsx` route registrations, nav entries, single
  env-var stubs) rather than mislabel them.
- **Instruction authoring:** each instruction authored individually (|real| ≤ 400),
  scoped to the one file, grounded in that file's real symbols, folding in PR
  intent — never reusing a whole PR/commit body across files.

## 3. Method (Phase 2)

- **Assignments (`make_synth_assignments.py` + `make_synth_topup.py`):** a
  deterministic matrix of **24 pattern families** × distinct **(entity, structural
  axes)** cells over a broad real-entity vocabulary (vendors, proposals, sourcing
  cases, vendor matches, evaluations, compliance audits, gate decisions, pilots,
  alerts, incidents, factsheets, …). Generic-utility families (rate limiter, retry
  decorator, pure-logic tests) vary **structurally only** — no entity field use.
- **Axes varied:** sync/async · retry (exp-jitter/fixed/none) · idempotency
  (key/version/none) · validation (strict/lenient) · return (result/throw) ·
  pagination (keyset/offset) · rate-limit algorithm · RLS (role/owner) ·
  observability (structured-log/metrics/audit).
- **Per-family cap ≤5%**; round-robin trimmed to the exact target.
- **Compile-verify (`verify_synth.py`)** — run on the **FULL** synthetic set, not
  just a 10% sample: `python -m py_compile` + `ruff --select E9,F` (Python),
  `esbuild` (JSX/JS), `sqlfluff --dialect postgres` (SQL). Failures dropped/fixed.

## 4. Security / redaction

- Tracked source is clean (0 JWT/sk-/AKIA; all secrets are env-reads). Line-by-line
  scan + redaction (`lib_secrets.py`) over **every** diff, instruction, and synthetic
  file: JWTs, sk-/sk-ant-, AKIA, Bearer tokens, secret-named assignments,
  private IPs, UUIDs, high-entropy blobs; env-reads and placeholders allow-listed.
- **Harvested infra-id literals** redacted everywhere: the tenant deployment hosts
  (`*.railway.app`, `*.vercel.app`, `smart-sourcing.devoneerstechnology.ai`). Public
  CDN/gov endpoints (fonts, OWASP, Dubai-gov, UAE PASS) kept as non-secret and
  load-bearing.
- Final secret sweep across all emitted files: **0 hits** (see `manifest.json`).

## 5. Tokenizer note (honest)

`tiktoken o200k_base` is the universal measuring stick. **Anthropic has no offline
tokenizer** (API-only since deprecation), so its sizes are this approximation,
clearly labeled; records sit far below the 16k cap so the choice does not bind. The
axolotl side would use its base model's HF tokenizer at train time; sizes here are
the same approximation.

## 6. Results

**Mix (final):** 210 real + 840 synthetic = **1050** records · **synthetic = 80.0%**
⚠️ (above the 70% line — your 4× choice). real:synthetic = 1 : 4.

**Phase 1 — real (210 pairs):** by language py 96 · jsx 90 · sql 16 · js 6 · css 2;
by kind whole 156 · new-file (chunked) 73 · split 14. Drawn from **48 PRs / 112
distinct files**. **0 apply-check failures** (every emitted diff verified to apply).
Dropped: 33 wiring/mount/stub fragments, 15 generated/lockfile/binary files, 1
irreducible monster hunk (listed in `decisions/dropped_monsters.json`), 1 doc-only
commit, 1 shallow-boundary commit.

**Phase 2 — synthetic:** 24 families authored 1092 candidate pairs (round 1: 35/family;
top-up: +12 to the 21 entity-parameterized families). **Compile-verify: 1092/1092 =
100.0%** with the repo toolchain (Python 669 via ruff+py_compile, SQL 235 via
sqlfluff-postgres, JSX 141 + JS 47 via esbuild); the spec's ≥10% sample = 100%. Many
families self-ran their own unit tests (e.g. pytest_logic 621 passing, pytest_service
117 passing).

**Dedup:** 134 exact + 10 near-duplicate (MinHash, Jaccard ≥ 0.9) removed — almost
entirely the generic-utility families hitting their legitimate variant ceiling
(pytest_logic, rate_limiter, retry_decorator) plus repeated entity+axis cells. Per
the dedup-over-padding principle, the deficit was refilled with genuinely distinct
top-up pairs rather than near-dups. **Round-robin trimmed to exactly 840** under a
per-family cap of 52 (5%); family distribution min 4 (pytest_logic ceiling) / max 40,
no empty family.

**Split:** deterministic 95/5, group-based (real grouped by PR, synth by id → no
source leakage). train 998 · eval 52 (4.95%). Shuffled within each split (seed 20240624).

**Tokens (anthropic full-render, o200k_base):** train min 258 / max 5065 / mean 1227;
eval 294 / 3367 / 1208. All records ≤16k (axolotl near-identical). Histograms in
`manifest.json`.

**Redaction:** 2 infra-host literals in real diffs; 27 high-entropy + 82 UUID example
literals in synthetic code, all replaced with safe placeholders (post-redaction code
still 100% compile-verifies). **Final secret sweep across all emitted files: 0 hits.**

**Validation:** independent `jq` parse + strict pass on all six emitted files →
**ALL VALID** (100% ASCII, no BOM, no blank lines, single trailing newline,
schema-correct roles, non-empty, no exact dups, ≤16k tokens).

**Rough training-cost estimate (very approximate):** ~1.0M training tokens/epoch for
the anthropic set (1050 records × ~1k tokens incl. system, train split ~998). At a
typical hosted LoRA SFT rate of ~$1–3 per 1M tokens, ~$1–3/epoch; 3 epochs ≈ $3–10.
axolotl/self-hosted on one A100 ≈ well under an hour for this size. Figures scale
linearly with epochs; treat as order-of-magnitude only.

## 7. Files

**Uploadable (handed as artifacts, NOT committed — see `manifest.json` for sha256):**
- `dist/train.anthropic.jsonl`, `dist/eval.anthropic.jsonl`
- `dist/train.axolotl.jsonl`, `dist/eval.axolotl.jsonl`

**Committed (this branch):** `finetune/generators/*.py`, `manifest.json`,
`report.md`, `smoke.anthropic.jsonl`, `smoke.axolotl.jsonl`,
`meta/*.meta.json`, `decisions/*.decisions.json`, `index/pairs.index.jsonl`.

`smoke.*.jsonl` (50 lines each) are for a trial upload only.

## 8. Reproduce

```
cd finetune/generators
export BATCH_DIR=… ASSIGN_DIR=… SYNTH_DIR=… ESBUILD=…
python3 extract_real.py && python3 curate_units.py          # Phase 1 units
#   (instructions authored by subagents -> real_pairs.jsonl via merge_real.py)
python3 make_synth_assignments.py && python3 make_synth_topup.py  # Phase 2 matrix
#   (code authored by subagents -> synth_pairs.jsonl via merge_synth.py)
python3 verify_synth.py        # full compile-verify
python3 build_dataset.py       # dedup -> cap -> split -> dual-schema emit
python3 validate_final.py      # independent jq + strict validation
```
Extraction, dedup, split, and shuffle are seed-deterministic; the LLM-authored
instruction/code layer is delivered as data (not bit-reproducible by nature).
