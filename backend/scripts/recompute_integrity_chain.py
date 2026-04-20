"""
One-shot recomputer for the chamber_ai_interactions integrity hash chain.

When a record's previous_hash becomes inconsistent (e.g. set to "GENESIS"
in the middle of the chain), this script walks forward from the first
broken record and rewrites previous_hash + integrity_hash so the chain
links up again.

Hash logic is imported from services.ai_interaction_service so that the
recompute is byte-for-byte identical to the production write path:

    content = f"{previous_hash}|{model_name}|{operation_type}|{total_tokens}|{cost_usd}|{timestamp}"
    integrity_hash = sha256(content).hexdigest()

Chain order matches verify_integrity(): ORDER BY timestamp ASC.

Usage:
    python -m backend.scripts.recompute_integrity_chain --dry-run
    python -m backend.scripts.recompute_integrity_chain
    python -m backend.scripts.recompute_integrity_chain --start-id f18b6d3f-89c1-43bc-a265-d5465523b1d7

The script is idempotent: a second run after a successful first run
should detect zero broken records and exit with "Chain already valid".
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

# Allow running as a standalone script (python backend/scripts/recompute_integrity_chain.py)
# as well as a module (python -m backend.scripts.recompute_integrity_chain).
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from database import supabase  # noqa: E402
from services.ai_interaction_service import _compute_integrity_hash  # noqa: E402


GENESIS = "GENESIS"
DEFAULT_START_ID = "f18b6d3f-89c1-43bc-a265-d5465523b1d7"


def fetch_all_records() -> list[dict]:
    """
    Fetch the entire chain in the same order verify_integrity() uses.
    Supabase caps rows per request, so page through with .range().
    """
    page_size = 1000
    offset = 0
    rows: list[dict] = []
    while True:
        resp = (
            supabase.table("chamber_ai_interactions")
            .select(
                "id, model_name, operation_type, prompt_tokens, completion_tokens, "
                "cost_usd, timestamp, integrity_hash, previous_hash"
            )
            .not_.is_("integrity_hash", "null")
            .order("timestamp", desc=False)
            .range(offset, offset + page_size - 1)
            .execute()
        )
        batch = resp.data or []
        rows.extend(batch)
        if len(batch) < page_size:
            break
        offset += page_size
    return rows


def find_first_break(records: list[dict]) -> Optional[int]:
    """Return the index of the first record whose chain link is broken."""
    for i, record in enumerate(records):
        expected_prev = records[i - 1]["integrity_hash"] if i > 0 else GENESIS
        total_tokens = (record.get("prompt_tokens") or 0) + (record.get("completion_tokens") or 0)
        expected_hash = _compute_integrity_hash(
            previous_hash=expected_prev,
            model_name=record["model_name"],
            operation_type=record["operation_type"],
            total_tokens=total_tokens,
            cost_usd=record["cost_usd"],
            timestamp=record["timestamp"],
        )
        if record["integrity_hash"] != expected_hash or record["previous_hash"] != expected_prev:
            return i
    return None


def find_index_by_id(records: list[dict], record_id: str) -> Optional[int]:
    for i, record in enumerate(records):
        if str(record["id"]) == record_id:
            return i
    return None


def recompute_from(records: list[dict], start_index: int, dry_run: bool) -> int:
    """
    Walk forward from start_index, rewriting previous_hash + integrity_hash
    so each record chains onto the last.

    Returns the number of records actually changed.
    """
    fixed = 0
    for i in range(start_index, len(records)):
        record = records[i]
        expected_prev = records[i - 1]["integrity_hash"] if i > 0 else GENESIS
        total_tokens = (record.get("prompt_tokens") or 0) + (record.get("completion_tokens") or 0)
        new_hash = _compute_integrity_hash(
            previous_hash=expected_prev,
            model_name=record["model_name"],
            operation_type=record["operation_type"],
            total_tokens=total_tokens,
            cost_usd=record["cost_usd"],
            timestamp=record["timestamp"],
        )

        already_correct = (
            record["previous_hash"] == expected_prev and record["integrity_hash"] == new_hash
        )
        if already_correct:
            # Keep the in-memory value stable for the next iteration.
            continue

        print(
            f"  [{i}] id={record['id']} "
            f"prev {record['previous_hash'][:12] if record['previous_hash'] else 'None'}… -> {expected_prev[:12]}…  "
            f"hash {record['integrity_hash'][:12]}… -> {new_hash[:12]}…"
        )

        if not dry_run:
            (
                supabase.table("chamber_ai_interactions")
                .update({"previous_hash": expected_prev, "integrity_hash": new_hash})
                .eq("id", record["id"])
                .execute()
            )

        # Mutate the in-memory copy so the next iteration chains off the NEW hash.
        record["previous_hash"] = expected_prev
        record["integrity_hash"] = new_hash
        fixed += 1

    return fixed


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Recompute σI integrity hash chain forward from a broken record."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print intended updates but do not write to the database.",
    )
    parser.add_argument(
        "--start-id",
        default=None,
        help=(
            "Record id to start recomputing from. "
            "If omitted, the script auto-detects the first broken record. "
            f"Default sentinel for this incident: {DEFAULT_START_ID}"
        ),
    )
    args = parser.parse_args()

    print("Fetching chamber_ai_interactions ordered by timestamp ASC…")
    records = fetch_all_records()
    print(f"Loaded {len(records)} hashed records.")

    if not records:
        print("No records to process.")
        return 0

    if args.start_id:
        start_index = find_index_by_id(records, args.start_id)
        if start_index is None:
            print(f"ERROR: --start-id {args.start_id} not found in chain.", file=sys.stderr)
            return 2
        print(f"Starting at explicit --start-id {args.start_id} (index {start_index}).")
    else:
        start_index = find_first_break(records)
        if start_index is None:
            print("Chain already valid. Nothing to do.")
            return 0
        print(
            f"First break detected at index {start_index}, "
            f"id={records[start_index]['id']}."
        )

    mode = "DRY RUN" if args.dry_run else "APPLYING UPDATES"
    print(f"\n{mode}: recomputing {len(records) - start_index} record(s) forward…\n")

    fixed = recompute_from(records, start_index, dry_run=args.dry_run)

    start_id = records[start_index]["id"]
    if args.dry_run:
        print(
            f"\nDry run complete. Would fix {fixed} record(s). "
            f"Chain would be restored from record {start_id} forward."
        )
    else:
        print(
            f"\nFixed {fixed} records. Chain integrity restored from record {start_id} forward."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
