#!/usr/bin/env python3
"""Run a SQL migration file against Supabase via the PostgREST RPC or psql.

Usage:
    python database/run_migration.py database/vendor_invite_migration.sql

Requires either:
  - SUPABASE_DB_URL env var (direct postgres connection string), OR
  - SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY env vars (uses REST SQL endpoint)
"""

import os
import sys
import subprocess


def run_via_psql(db_url: str, sql: str) -> None:
    """Execute SQL via psql."""
    result = subprocess.run(
        ["psql", db_url, "-c", sql],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"psql error: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    print(result.stdout)


def run_via_rest(supabase_url: str, service_key: str, sql: str) -> None:
    """Execute SQL via Supabase REST SQL endpoint (requires service role key)."""
    import urllib.request
    import json

    url = f"{supabase_url}/rest/v1/rpc/exec_sql"
    headers = {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Content-Type": "application/json",
    }
    data = json.dumps({"query": sql}).encode()
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            print(f"Success ({resp.status}): {resp.read().decode()}")
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"REST error {e.code}: {body}", file=sys.stderr)
        print(
            "\nIf exec_sql RPC doesn't exist, run this SQL directly in the "
            "Supabase SQL Editor (Dashboard > SQL Editor).",
            file=sys.stderr,
        )
        sys.exit(1)


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <migration_file.sql>", file=sys.stderr)
        sys.exit(1)

    sql_file = sys.argv[1]
    with open(sql_file) as f:
        sql = f.read()

    print(f"Running migration: {sql_file}")
    print("-" * 40)

    db_url = os.environ.get("SUPABASE_DB_URL", "").strip()
    if db_url:
        print("Using direct PostgreSQL connection (SUPABASE_DB_URL)...")
        run_via_psql(db_url, sql)
        return

    supabase_url = os.environ.get("SUPABASE_URL", "").strip()
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    if supabase_url and service_key:
        print("Using Supabase REST endpoint...")
        run_via_rest(supabase_url, service_key, sql)
        return

    print(
        "ERROR: Set SUPABASE_DB_URL (preferred) or SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY.\n"
        "Alternatively, paste the SQL below into the Supabase SQL Editor:\n",
        file=sys.stderr,
    )
    print(sql)
    sys.exit(1)


if __name__ == "__main__":
    main()
