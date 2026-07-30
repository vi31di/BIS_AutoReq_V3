"""
compare_audit_runs.py — proves a fix worked, catches regressions
====================================================================

After you fix a root-cause rule and re-run the full evaluator, this
script diffs the latest run against the previous one, per check_name/
reason_code cluster.

Usage:
    python compare_audit_runs.py --dsn postgresql://... --script validate_ocr_quality
    python compare_audit_runs.py --dsn postgresql://... --script validate_resolution_engine
    python compare_audit_runs.py (uses default sqlite)
"""

import argparse
import asyncio
from typing import Optional

from api.db import DBConnection, init_db_connection


async def compare(dsn: Optional[str], script_name: str):
    if dsn:
        import os
        os.environ["DATABASE_URL"] = dsn
    await init_db_connection()

    async with DBConnection() as db:
        runs = await db.fetch(
            "SELECT run_id, run_at, total_checked, total_flagged FROM audit_runs "
            "WHERE script_name = $1 ORDER BY run_id DESC LIMIT 2",
            script_name,
        )
        if len(runs) < 2:
            print(f"Need at least 2 runs of '{script_name}' to compare — only found {len(runs)}.")
            return

        latest, previous = runs[0], runs[1]
        print(f"\nComparing run {previous['run_id']} ({previous['run_at']}) "
              f"→ run {latest['run_id']} ({latest['run_at']})")
        print(f"Total flagged: {previous['total_flagged']} → {latest['total_flagged']}")

        if script_name == "validate_ocr_quality":
            table, group_col = "review_queue", "check_name"
        else:
            table, group_col = "resolution_audit_mismatches", "reason_code"

        counts = await db.fetch(f"""
            SELECT run_id, {group_col} AS cluster, COUNT(*) AS n
            FROM {table}
            WHERE run_id IN ($1, $2)
            GROUP BY run_id, {group_col}
        """, previous["run_id"], latest["run_id"])

        prev_counts = {r["cluster"]: r["n"] for r in counts if r["run_id"] == previous["run_id"]}
        latest_counts = {r["cluster"]: r["n"] for r in counts if r["run_id"] == latest["run_id"]}
        all_clusters = set(prev_counts) | set(latest_counts)

        print(f"\n{'Cluster':40s} {'Before':>8s} {'After':>8s} {'Change':>10s}")
        print("-" * 70)
        regressions = []
        for cluster in sorted(all_clusters, key=lambda c: -(latest_counts.get(c, 0) - prev_counts.get(c, 0))):
            before = prev_counts.get(cluster, 0)
            after = latest_counts.get(cluster, 0)
            delta = after - before
            marker = ""
            if before == 0 and after > 0:
                marker = "  ← NEW (possible regression)"
                regressions.append(cluster)
            elif delta < 0:
                marker = "  ✓ improved"
            print(f"{cluster:40s} {before:>8d} {after:>8d} {delta:>+10d}{marker}")

        if regressions:
            print(f"\n⚠ {len(regressions)} NEW cluster(s) appeared that weren't present in the "
                  f"previous run. Investigate before treating this fix as complete — a rule "
                  f"change can fix one failure mode while introducing another.")
        else:
            print(f"\nNo new clusters appeared — the fix did not introduce a visible regression "
                  f"in this pass.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dsn", default=None)
    parser.add_argument("--script", required=True,
                         choices=["validate_ocr_quality", "validate_resolution_engine"])
    args = parser.parse_args()
    asyncio.run(compare(args.dsn, args.script))
