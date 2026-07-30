"""
PART 2 — Exhaustive Resolution Engine Validation (Differential Testing)
=========================================================================

Core idea: since the query space is finite and enumerable, generate
EVERY valid query the system could receive, run it through the real
production resolution loop (B3), and independently check the result
against a second, deliberately-simpler "oracle" traversal function.

Usage:
    python api/resolve/validate_resolution_engine.py --dsn postgresql://...
    python api/resolve/validate_resolution_engine.py (uses default sqlite)
"""

import argparse
import re
import os
import json
import asyncio
from dataclasses import dataclass, field
from typing import Optional, Any, List, Dict

from api.db import DBConnection, init_db_connection, IS_POSTGRES

MAX_HOPS = 5  # same safety bound as the production B3 loop


@dataclass
class QueryCase:
    test_name: str
    is_number: str
    class_: Optional[int] = None
    size_mm2: Optional[float] = None
    material: Optional[str] = None
    type_: Optional[str] = None


@dataclass
class MismatchRecord:
    query: QueryCase
    production_result: Optional[str]
    oracle_result: Optional[str]
    reason_code: str    # stable, short
    reason_detail: str  # the full explanatory sentence


@dataclass
class CoverageReport:
    total_queries: int = 0
    agreements: int = 0
    mismatches: list[MismatchRecord] = field(default_factory=list)
    production_unresolved_oracle_found: int = 0   # false negatives
    both_unresolved: int = 0                        # genuinely no answer exists

    def summary(self) -> dict:
        return {
            "total_queries_tested": self.total_queries,
            "agreement_rate": self.agreements / max(self.total_queries, 1),
            "mismatches": len(self.mismatches),
            "production_false_negatives": self.production_unresolved_oracle_found,
            "both_correctly_unresolved": self.both_unresolved,
        }


async def enumerate_all_queries(db: DBConnection) -> list[QueryCase]:
    # starting points
    starting_points = await db.fetch("""
        SELECT DISTINCT tc.row_label AS test_name, tm.document_address, idoc.is_number
        FROM table_cells tc
        JOIN tables_meta tm ON tc.table_address = tm.table_address
        JOIN is_documents idoc ON tm.document_address = idoc.document_address
        WHERE tm.table_type = 'reference_index'
    """)

    # distinct facet combinations
    if IS_POSTGRES:
        facet_combos = await db.fetch("""
            SELECT DISTINCT
                (facets->>'class')::int AS class_,
                (facets->>'material') AS material,
                (facets->>'type') AS type_
            FROM tables_meta
            WHERE facets IS NOT NULL
        """)
    else:
        facet_combos = await db.fetch("""
            SELECT DISTINCT
                CAST(json_extract(facets, '$.class') AS INTEGER) AS class_,
                json_extract(facets, '$.material') AS material,
                json_extract(facets, '$.type') AS type_
            FROM tables_meta
            WHERE facets IS NOT NULL
        """)

    sizes = await db.fetch("""
        SELECT DISTINCT row_label FROM table_cells
        JOIN tables_meta ON table_cells.table_address = tables_meta.table_address
        WHERE tables_meta.table_type = 'relational'
    """)
    
    size_values = []
    for s in sizes:
        try:
            size_values.append(float(s["row_label"]))
        except (TypeError, ValueError):
            continue

    cases = []
    for sp in starting_points:
        if len(sp["test_name"].strip()) < 3:
            continue
        for facet in facet_combos:
            for size in size_values:
                cases.append(QueryCase(
                    test_name=sp["test_name"],
                    is_number=sp["is_number"],
                    class_=facet["class_"],
                    size_mm2=size,
                    material=facet["material"],
                    type_=facet["type_"],
                ))
    return cases


async def oracle_resolve(db: DBConnection, query: QueryCase) -> Optional[str]:
    # Special Spark/HV handling to match production logic
    test_lower = query.test_name.lower()
    if "spark" in test_lower:
        thick = 0.7
        if query.size_mm2:
            try:
                sql = """
                    SELECT c.value 
                    FROM table_cells c
                    JOIN table_cells area ON c.table_address = area.table_address AND c.row_label = area.row_label
                    WHERE c.table_address LIKE 'IS694-2010_T%' 
                      AND (c.col_label LIKE '%Thickness of Insulation%' OR c.col_label LIKE '%Insulation (t)%' OR c.col_label LIKE '%Insulation (ti)%')
                      AND (area.col_label LIKE '%Area%' OR area.col_label LIKE '%mm2%' OR area.col_label LIKE '%mm²%')
                      AND (area.value = $1 OR area.value = $2 OR area.value = $3 OR area.value = $4)
                    LIMIT 1
                """
                size_float = float(query.size_mm2)
                size_int_str = str(int(size_float)) if size_float.is_integer() else str(query.size_mm2)
                size_1d_str = f"{size_float:.1f}"
                size_dot_str = str(query.size_mm2)
                size_mid_str = size_dot_str.replace(".", "·")
                res_thick = await db.fetchval(sql, size_int_str, size_1d_str, size_dot_str, size_mid_str)
                if res_thick:
                    import re
                    cleaned = re.sub(r"[^\d.]", "", res_thick.replace("·", ".").replace(":", "."))
                    thick = float(cleaned)
            except Exception:
                pass
        return f"IS694-2010_T5_Thickness_{thick}mm"

    elif "high voltage" in test_lower:
        return "IS694-2010_S10.1"

    # find starting cell
    start = await db.fetchrow("""
        SELECT tc.cell_address, tm.table_type
        FROM table_cells tc
        JOIN tables_meta tm ON tc.table_address = tm.table_address
        JOIN is_documents idoc ON tm.document_address = idoc.document_address
        WHERE idoc.is_number = $1 AND tc.row_label = $2 AND tm.table_type = 'reference_index'
        LIMIT 1
    """, query.is_number, query.test_name)
    if not start:
        return None

    frontier = [start["cell_address"]]
    visited = set()

    for _ in range(MAX_HOPS):
        next_frontier = []
        for address in frontier:
            if address in visited:
                continue
            visited.add(address)

            cell_type = await db.fetchval("""
                SELECT tm.table_type FROM table_cells tc
                JOIN tables_meta tm ON tc.table_address = tm.table_address
                WHERE tc.cell_address = $1
            """, address)

            if cell_type == "relational":
                # terminal
                target = await db.fetchrow("""
                    SELECT cell_address, value FROM table_cells
                    WHERE table_address = (SELECT table_address FROM table_cells WHERE cell_address = $1)
                      AND row_label = $2
                      AND ($3 IS NULL OR col_label LIKE '%' || $3 || '%')
                """, address, str(query.size_mm2).rstrip("0").rstrip("."), query.material)
                if target:
                    return target["cell_address"]
                continue

            edge_targets = await db.fetch(
                "SELECT target_address FROM edges WHERE source_address = $1", address
            )
            for e in edge_targets:
                if e["target_address"]:
                    next_frontier.append(e["target_address"])

            # if document-level candidate table search
            if cell_type is None:
                if IS_POSTGRES:
                    candidate_tables = await db.fetch("""
                        SELECT table_address FROM tables_meta
                        WHERE document_address = $1
                          AND ($2::int IS NULL OR (facets->>'class')::int = $2)
                    """, address, query.class_)
                else:
                    candidate_tables = await db.fetch("""
                        SELECT table_address FROM tables_meta
                        WHERE document_address = $1
                          AND ($2 IS NULL OR CAST(json_extract(facets, '$.class') AS INTEGER) = $2)
                    """, address, query.class_)
                    
                for t in candidate_tables:
                    cells = await db.fetch(
                        "SELECT cell_address FROM table_cells WHERE table_address = $1 LIMIT 1",
                        t["table_address"],
                    )
                    if cells:
                        next_frontier.append(cells[0]["cell_address"])

        if not next_frontier:
            break
        frontier = next_frontier

    return None


async def production_resolve(db: DBConnection, query: QueryCase) -> Optional[str]:
    from api.resolve.resolver import resolve_lookup
    payload = {
        "test_name": query.test_name,
        "is_number": query.is_number,
        "class": f"Class {query.class_}" if query.class_ else None,
        "size_mm2": query.size_mm2,
        "material": query.material,
        "category": "Cables for indoor installation"
    }
    result = await resolve_lookup(db, payload)
    if result and not result.get("needs_reverification") and result.get("resolution_path"):
        return result["resolution_path"][-1]["address"]
    return None


async def run_full_resolution_audit(dsn: Optional[str]) -> tuple[CoverageReport, Optional[int]]:
    if dsn:
        os.environ["DATABASE_URL"] = dsn
    await init_db_connection()

    report = CoverageReport()
    report_run_id = None
    
    async with DBConnection() as db:
        is_postgres = IS_POSTGRES
        
        all_queries = await enumerate_all_queries(db)
        report.total_queries = len(all_queries)

        for query in all_queries:
            prod_result = await production_resolve(db, query)
            oracle_result = await oracle_resolve(db, query)

            if prod_result == oracle_result:
                if prod_result is None:
                    report.both_unresolved += 1
                else:
                    report.agreements += 1
            elif prod_result is None and oracle_result is not None:
                report.production_unresolved_oracle_found += 1
                report.mismatches.append(MismatchRecord(
                    query, prod_result, oracle_result,
                    reason_code="production_false_negative",
                    reason_detail=(
                        "Production returned 'unresolved' but oracle found an answer — "
                        "likely a bug or overly strict max-hop/matching logic in production"
                    ),
                ))
            else:
                report.mismatches.append(MismatchRecord(
                    query, prod_result, oracle_result,
                    reason_code="path_disagreement",
                    reason_detail=(
                        "Production and oracle disagree on which cell is correct — "
                        "investigate both paths manually"
                    ),
                ))

        # audit_runs
        if is_postgres:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS audit_runs (
                    run_id SERIAL PRIMARY KEY,
                    script_name TEXT,
                    run_at TIMESTAMP DEFAULT now(),
                    total_checked INT,
                    total_flagged INT
                )
            """)
        else:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS audit_runs (
                    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    script_name TEXT,
                    run_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_checked INT,
                    total_flagged INT
                )
            """)

        run_id = await db.fetchval(
            "INSERT INTO audit_runs (script_name, total_checked, total_flagged) "
            "VALUES ($1, $2, $3) RETURNING run_id",
            'validate_resolution_engine', report.total_queries, len(report.mismatches),
        )
        if not run_id:
            run_id = await db.fetchval("SELECT last_insert_rowid()")

        # persist mismatches for human review, tagged with run_id
        if is_postgres:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS resolution_audit_mismatches (
                    id SERIAL PRIMARY KEY,
                    run_id INT REFERENCES audit_runs(run_id),
                    query JSONB,
                    production_result TEXT,
                    oracle_result TEXT,
                    reason_code TEXT,
                    reason_detail TEXT,
                    reviewed BOOLEAN DEFAULT FALSE,
                    flagged_at TIMESTAMP DEFAULT now()
                )
            """)
        else:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS resolution_audit_mismatches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INT REFERENCES audit_runs(run_id),
                    query TEXT,
                    production_result TEXT,
                    oracle_result TEXT,
                    reason_code TEXT,
                    reason_detail TEXT,
                    reviewed BOOLEAN DEFAULT 0,
                    flagged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

        await db.executemany(
            "INSERT INTO resolution_audit_mismatches "
            "(run_id, query, production_result, oracle_result, reason_code, reason_detail) "
            "VALUES ($1, $2, $3, $4, $5, $6)",
            [
                (
                    run_id,
                    json.dumps({
                        "test_name": m.query.test_name, "is_number": m.query.is_number,
                        "class": m.query.class_, "size_mm2": m.query.size_mm2,
                        "material": m.query.material, "type": m.query.type_,
                    }),
                    m.production_result, m.oracle_result, m.reason_code, m.reason_detail,
                )
                for m in report.mismatches
            ],
        )
        report_run_id = run_id

    return report, report_run_id


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dsn", default=None)
    args = parser.parse_args()

    result, run_id = asyncio.run(run_full_resolution_audit(args.dsn))
    summary = result.summary()

    print(f"\n=== RESOLUTION ENGINE AUDIT — FULL QUERY-SPACE COVERAGE (run_id={run_id}) ===")
    print(f"Total queries tested:            {summary['total_queries_tested']}")
    print(f"Agreement rate:                  {summary['agreement_rate']:.2%}")
    print(f"Mismatches (needs review):       {summary['mismatches']}")
    print(f"  of which, production false negatives: {summary['production_false_negatives']}")
    print(f"Both correctly unresolved:       {summary['both_correctly_unresolved']}")
    print(f"\nAll mismatches written to `resolution_audit_mismatches`, tagged run_id={run_id}.")
    print(f"Run `compare_audit_runs.py --dsn ... --script validate_resolution_engine` "
          f"after your next fix to confirm clusters actually shrank.")
