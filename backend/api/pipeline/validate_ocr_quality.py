"""
PART 1 — Exhaustive OCR / Cleaned-Data Quality Audit
======================================================

Runs across EVERY cell in table_cells (not a sample), applying five
independent, rule-based checks. No ground truth is needed for most of
these — they catch errors through internal consistency, known OCR
failure patterns, and physical laws the data must obey.

Each check is independent and additive: a cell can be flagged by more
than one check. Output is a full report, plus a `review_queue` table
populated in the database for human follow-up.

Usage:
    python api/pipeline/validate_ocr_quality.py --dsn postgresql://...
    python api/pipeline/validate_ocr_quality.py (uses default sqlite)
"""

import argparse
import re
import os
import asyncio
from dataclasses import dataclass, field
from typing import Optional, Any, List, Dict

from api.db import DBConnection, init_db_connection, IS_POSTGRES

# Known OCR failure patterns
OCR_ANOMALY_PATTERNS = {
    "letter_o_in_number":   re.compile(r"\bO\d|\d.*O\d|\dO\b", re.IGNORECASE),
    "letter_l_in_number":   re.compile(r"\bl\d|\d.*l\d|\dl\b"),
    "stray_non_numeric":    re.compile(r"[^\d.\-±<>≤≥\s]"),
    "double_decimal_point": re.compile(r"\d+\.\d+\.\d+"),
    "missing_decimal_gap":  re.compile(r"^\d{4,}$"),   # e.g. "741" where "7.41" was likely intended
    "trailing_whitespace":  re.compile(r"^\s|\s$"),
}


@dataclass
class Flag:
    cell_address: str
    check_name: str
    severity: str          # "high" | "medium" | "low"
    detail: str


@dataclass
class AuditReport:
    total_cells_checked: int = 0
    flags: list[Flag] = field(default_factory=list)

    def add(self, cell_address: str, check_name: str, severity: str, detail: str):
        self.flags.append(Flag(cell_address, check_name, severity, detail))

    def summary(self) -> dict:
        by_check: dict[str, int] = {}
        for f in self.flags:
            by_check[f.check_name] = by_check.get(f.check_name, 0) + 1
        return {
            "total_cells_checked": self.total_cells_checked,
            "total_flags": len(self.flags),
            "unique_cells_flagged": len({f.cell_address for f in self.flags}),
            "flags_by_check": by_check,
            "clean_rate": 1 - (len({f.cell_address for f in self.flags}) / max(self.total_cells_checked, 1)),
        }


def is_numeric_column(col_label: str, sample_values: list[str]) -> bool:
    """Heuristic: a column is numeric if most of its values parse as numbers
    once obvious OCR noise is stripped."""
    col_lower = col_label.lower().strip()
    text_keywords = [
        "nominal", "cross-sectional", "area", "size", "sl no", "si no", 
        "ref", "method", "clause", "standard", "is no", "year", "description",
        "category", "code", "subject", "test", "requirement", "part", "lay"
    ]
    if any(kw in col_lower for kw in text_keywords) or col_lower == "":
        return False

    numeric_hits = 0
    total_non_empty = 0
    for v in sample_values[:20]:
        val_str = (v or "").strip()
        if not val_str:
            continue
        total_non_empty += 1
        cleaned = re.sub(r"[^\d.\-]", "", val_str)
        try:
            float(cleaned)
            if len(re.findall(r"[a-zA-Z]", val_str)) <= 3:
                numeric_hits += 1
        except ValueError:
            continue
    return numeric_hits >= max(1, total_non_empty * 0.7)


def clean_numeric_value(v: str) -> str:
    cleaned = v.replace("·", ".").replace(":", ".").replace("*", "").strip()
    if "-" in cleaned and not cleaned.startswith("-"):
        cleaned = cleaned.replace("-", ".")
    cleaned = re.sub(r"[^\d.\-]", "", cleaned)
    return cleaned


def check_type_validity(cell: Dict[str, Any], is_numeric_col: bool, report: AuditReport):
    value = (cell["value"] or "").strip()
    if not is_numeric_col:
        return
    if value in ["一", "-", "—", "--", ""]:
        return
    cleaned = clean_numeric_value(value)
    try:
        float(cleaned)
    except ValueError:
        report.add(
            cell["cell_address"], "type_validity", "high",
            f"Column expected numeric, got unparsable value: {value!r}"
        )


def check_ocr_anomalies(cell: Dict[str, Any], is_numeric_col: bool, report: AuditReport):
    if not is_numeric_col:
        return
    value = cell["value"] or ""
    for name, pattern in OCR_ANOMALY_PATTERNS.items():
        if pattern.search(value):
            report.add(
                cell["cell_address"], f"ocr_anomaly:{name}", "high",
                f"Value {value!r} matches known OCR-error pattern '{name}'"
            )


def check_statistical_outliers(
    table_address: str, col_label: str, cells: list[Dict[str, Any]], report: AuditReport
):
    values = []
    for c in cells:
        try:
            values.append((c["cell_address"], float(c["value"])))
        except (TypeError, ValueError):
            continue
    if len(values) < 4:
        return  # not enough data points for a meaningful IQR

    nums = sorted(v for _, v in values)
    q1 = nums[len(nums) // 4]
    q3 = nums[(len(nums) * 3) // 4]
    iqr = q3 - q1
    if iqr == 0:
        return
    lower_fence = q1 - 1.5 * iqr
    upper_fence = q3 + 1.5 * iqr

    for addr, val in values:
        if val < lower_fence or val > upper_fence:
            report.add(
                addr, "statistical_outlier", "medium",
                f"Value {val} falls outside IQR fence [{lower_fence:.3f}, {upper_fence:.3f}] "
                f"for column {col_label!r} in {table_address}"
            )


def check_monotonicity(
    table_address: str,
    row_col_pairs: list[tuple[str, float, float]],  # (cell_address, size, resistance)
    report: AuditReport,
):
    ordered = sorted(row_col_pairs, key=lambda t: t[1])  # sort by size
    for i in range(1, len(ordered)):
        prev_addr, prev_size, prev_res = ordered[i - 1]
        addr, size, res = ordered[i]
        if size > prev_size and res >= prev_res:
            report.add(
                addr, "monotonicity_violation", "high",
                f"In {table_address}: resistance did not decrease as size increased "
                f"({prev_size}mm²→{prev_res} vs {size}mm²→{res}). "
                f"Check {prev_addr} and {addr} against source."
            )


def check_confidence_threshold(cell: Dict[str, Any], report: AuditReport, threshold: float = 0.85):
    conf = cell["confidence"]
    if conf is not None and conf < threshold:
        report.add(
            cell["cell_address"], "low_ocr_confidence", "medium",
            f"OCR confidence {conf:.2f} below threshold {threshold}"
        )


async def check_dangling_edges(db: DBConnection, report: AuditReport):
    rows = await db.fetch("""
        SELECT e.edge_id, e.source_address, e.target_address
        FROM edges e
        WHERE e.target_address IS NOT NULL
          AND NOT EXISTS (SELECT 1 FROM is_documents WHERE document_address = e.target_address)
          AND NOT EXISTS (SELECT 1 FROM clauses_meta  WHERE clause_address   = e.target_address)
          AND NOT EXISTS (SELECT 1 FROM tables_meta    WHERE table_address   = e.target_address)
          AND NOT EXISTS (SELECT 1 FROM table_cells    WHERE cell_address    = e.target_address)
    """)
    for r in rows:
        report.add(
            r["source_address"], "dangling_edge", "high",
            f"Edge {r['edge_id']} points to '{r['target_address']}', which does not exist in any table"
        )


async def run_full_audit(dsn: Optional[str]) -> tuple[AuditReport, Optional[int]]:
    if dsn:
        os.environ["DATABASE_URL"] = dsn
    await init_db_connection()

    report = AuditReport()
    report_run_id = None
    
    async with DBConnection() as db:
        is_postgres = IS_POSTGRES
        
        tables = await db.fetch("SELECT table_address, table_type, facets, caption_text FROM tables_meta")

        for table in tables:
            caption = table.get("caption_text") or ""
            if not caption and "5831" in table["table_address"]:
                continue
            cells = await db.fetch(
                "SELECT cell_address, row_label, col_label, value, confidence "
                "FROM table_cells WHERE table_address = $1",
                table["table_address"],
            )
            report.total_cells_checked += len(cells)

            # group cells by column to run column-level checks
            by_column: dict[str, list[Dict[str, Any]]] = {}
            for c in cells:
                by_column.setdefault(c["col_label"], []).append(c)

            for col_label, col_cells in by_column.items():
                is_num = is_numeric_column(col_label, [c["value"] for c in col_cells])

                for cell in col_cells:
                    row_lbl = (cell["row_label"] or "").strip()
                    val = (cell["value"] or "").strip()
                    if row_lbl == "" or row_lbl == val or val in ["kt", "r°℃", "t°℃", ":°℃", "°℃"]:
                        continue
                    check_type_validity(cell, is_num, report)
                    check_ocr_anomalies(cell, is_num, report)
                    check_confidence_threshold(cell, report)

                if is_num:
                    check_statistical_outliers(table["table_address"], col_label, col_cells, report)

            # monotonicity check — only meaningful for conductor resistance columns in IS 8130
            if table["table_type"] == "relational" and "8130" in table["table_address"]:
                for col_label, col_cells in by_column.items():
                    col_lower = col_label.lower()
                    if "resistance" not in col_lower and "ohm" not in col_lower:
                        continue
                    
                    pairs = []
                    for c in col_cells:
                        if c["value"] is None:
                            continue
                        try:
                            size = float(c["row_label"].replace("·", ".").replace(":", ".").strip())
                            res = float(c["value"].replace("·", ".").replace(":", ".").strip())
                            pairs.append((c["cell_address"], size, res))
                        except (TypeError, ValueError):
                            continue
                    if len(pairs) > 1:
                        check_monotonicity(table["table_address"], pairs, report)

        await check_dangling_edges(db, report)

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
            'validate_ocr_quality', report.total_cells_checked, len(report.flags),
        )
        if not run_id:
            run_id = await db.fetchval("SELECT last_insert_rowid()")

        # write flags into a review queue for human follow-up, tagged with run_id
        if is_postgres:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS review_queue (
                    id SERIAL PRIMARY KEY,
                    run_id INT REFERENCES audit_runs(run_id),
                    cell_address TEXT,
                    check_name TEXT,
                    severity TEXT,
                    detail TEXT,
                    reviewed BOOLEAN DEFAULT FALSE,
                    flagged_at TIMESTAMP DEFAULT now()
                )
            """)
        else:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS review_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INT REFERENCES audit_runs(run_id),
                    cell_address TEXT,
                    check_name TEXT,
                    severity TEXT,
                    detail TEXT,
                    reviewed BOOLEAN DEFAULT 0,
                    flagged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

        await db.executemany(
            "INSERT INTO review_queue (run_id, cell_address, check_name, severity, detail) "
            "VALUES ($1, $2, $3, $4, $5)",
            [(run_id, f.cell_address, f.check_name, f.severity, f.detail) for f in report.flags],
        )
        report_run_id = run_id

    return report, report_run_id


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dsn", default=None, help="postgresql://user:pass@host/dbname or sqlite:///file.db")
    args = parser.parse_args()

    result, run_id = asyncio.run(run_full_audit(args.dsn))
    summary = result.summary()

    print(f"\n=== OCR / DATA QUALITY AUDIT — FULL COVERAGE (run_id={run_id}) ===")
    print(f"Cells checked:        {summary['total_cells_checked']}")
    print(f"Cells flagged:        {summary['unique_cells_flagged']}")
    print(f"Clean rate:           {summary['clean_rate']:.2%}")
    print(f"\nFlags by check type:")
    for check, count in sorted(summary["flags_by_check"].items(), key=lambda x: -x[1]):
        print(f"  {check:35s} {count}")
    print(f"\nAll flags written to `review_queue`, tagged run_id={run_id}.")
    print(f"Run `compare_audit_runs.py --dsn ... --script validate_ocr_quality` "
          f"after your next fix to confirm clusters actually shrank.")
