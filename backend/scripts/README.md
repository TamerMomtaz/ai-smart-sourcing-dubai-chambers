# backend/scripts

One-shot operational scripts. Not imported by the running service.

## recompute_integrity_chain.py

Rewrites `chamber_ai_interactions.previous_hash` + `integrity_hash` for every
record from the first broken link forward, using the production hash function
in `services.ai_interaction_service._compute_integrity_hash`.

### When to use

Run only after the σI Transparency dashboard reports an "Integrity Break
Detected" and you have confirmed the break is caused by a bad row in the
middle of the chain (not by tampering with historical data you need to
preserve as-is). The script does not remove or add rows; it only relinks
the chain.

### Usage

```bash
# From the repo root on the backend host (Railway shell, local dev, etc.)
# with SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in the environment.

# 1. Dry run — prints the exact rows and hashes it would write.
python -m backend.scripts.recompute_integrity_chain --dry-run

# 2. Apply.
python -m backend.scripts.recompute_integrity_chain

# Optional: force the start point instead of auto-detecting.
python -m backend.scripts.recompute_integrity_chain \
    --start-id f18b6d3f-89c1-43bc-a265-d5465523b1d7
```

### Guarantees

- **Idempotent.** Running the script twice after a successful run prints
  "Chain already valid. Nothing to do." and performs no writes.
- **Hash parity.** The script imports `_compute_integrity_hash` directly
  from the production service module — the string format and SHA-256
  digest are byte-for-byte identical to what the write path produces.
- **Forward-only.** Records before the break are never modified.
- **Order matches verifier.** Rows are processed in `timestamp ASC`
  order, the same ordering used by `verify_integrity()`.

### What to verify after running

1. Hit the σI Transparency endpoint / dashboard — the "Integrity Break
   Detected" banner should clear.
2. `GET` `verify_integrity()` output should report `chain_valid: true`
   and `first_broken_at: null`.
