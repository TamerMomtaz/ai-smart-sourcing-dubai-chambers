# HOW TO UPLOAD — read first

This dataset ships the **same 1050 pairs in TWO schemas**. For any one fine-tune
job, upload **exactly one schema's two files**. Never mix schemas in one job, and
never upload the metadata files.

Every training file is valid newline-delimited JSON — one object per line, **0
unparsable lines**. sha256 + record counts + token histograms are in `manifest.json`.

## Fine-tuning on HF / axolotl  → upload ONLY these two
- `dist/train.axolotl.jsonl`  (998 records)
- `dist/eval.axolotl.jsonl`   (52 records)
- trial run first (optional): `smoke.axolotl.jsonl` (50 records, same schema)

Schema per line: `{"messages":[{"role":"system",...},{"role":"user",...},{"role":"assistant",...}]}`
(axolotl `chat_template` dataset type).

## Fine-tuning on Anthropic Messages  → upload ONLY these two
- `dist/train.anthropic.jsonl` (998)
- `dist/eval.anthropic.jsonl`  (52)
- trial run first (optional): `smoke.anthropic.jsonl` (50)

Schema per line: `{"system":"...","messages":[{"role":"user",...},{"role":"assistant",...}]}`

## DO NOT UPLOAD — these are NOT training data
- **`manifest.json`** — metadata (a single pretty-printed JSON object). A JSONL
  validator reports ~111 "unparsable" lines because it is not line-delimited. Use it
  only to check sha256/counts.
- `report.md`, `meta/*.json`, `decisions/*.json`, `index/pairs.index.jsonl` —
  provenance/metadata, never uploaded.

## "Why was my axolotl eval flagged as a duplicate?"
Because the `.anthropic` and `.axolotl` files contain the **same pairs** in
different wrappers. If you upload both into the same project/job, the platform's
content de-dup flags the second one. Upload one schema only. (Within a single
schema there is **no** train↔eval overlap — verified.)
