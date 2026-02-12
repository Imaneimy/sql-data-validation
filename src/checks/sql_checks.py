"""
SQL Data Quality Checks
Runs SQL-based assertions against a SQLite database (simulates PostgreSQL/Hive).
Each check returns a CheckResult with pass/fail status and details.
"""

import sqlite3
from dataclasses import dataclass, field
from typing import List, Optional, Any
import logging

logger = logging.getLogger(__name__)


@dataclass
class CheckResult:
    check_id: str
    check_name: str
    table: str
    column: Optional[str]
    passed: bool
    expected: Any
    actual: Any
    details: str = ""
    severity: str = "HIGH"   # HIGH | MEDIUM | LOW

    def to_dict(self) -> dict:
        return {
            "check_id": self.check_id,
            "check_name": self.check_name,
            "table": self.table,
            "column": self.column or "—",
            "passed": "PASS" if self.passed else "FAIL",
            "expected": str(self.expected),
            "actual": str(self.actual),
            "details": self.details,
            "severity": self.severity,
        }


class SQLQualityChecker:
    """Runs data quality checks against a SQLite connection."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self.results: List[CheckResult] = []

    def _execute(self, sql: str) -> Any:
        cursor = self.conn.cursor()
        cursor.execute(sql)
        row = cursor.fetchone()
        return row[0] if row else None

    # ── Completeness ────────────────────────────────────────────────────────

    def check_not_null(self, check_id: str, table: str, column: str,
                       severity: str = "HIGH") -> CheckResult:
        """Assert column contains no NULL values."""
        count = self._execute(f"SELECT COUNT(*) FROM {table} WHERE {column} IS NULL")
        result = CheckResult(
            check_id=check_id,
            check_name="NOT NULL",
            table=table, column=column,
            passed=count == 0,
            expected=0, actual=count,
            details=f"{count} NULL value(s) found" if count else "No NULLs detected",
            severity=severity,
        )
        self.results.append(result)
        return result

    def check_completeness_rate(self, check_id: str, table: str, column: str,
                                min_rate: float = 0.95, severity: str = "MEDIUM") -> CheckResult:
        """Assert that at least `min_rate` fraction of rows are non-null."""
        total = self._execute(f"SELECT COUNT(*) FROM {table}")
        non_null = self._execute(f"SELECT COUNT({column}) FROM {table}")
        rate = non_null / total if total else 0.0
        result = CheckResult(
            check_id=check_id,
            check_name="COMPLETENESS RATE",
            table=table, column=column,
            passed=rate >= min_rate,
            expected=f">= {min_rate:.0%}", actual=f"{rate:.2%}",
            details=f"{non_null}/{total} non-null rows",
            severity=severity,
        )
        self.results.append(result)
        return result

    # ── Uniqueness ──────────────────────────────────────────────────────────

    def check_uniqueness(self, check_id: str, table: str, column: str,
                         severity: str = "HIGH") -> CheckResult:
        """Assert all values in the column are distinct."""
        total = self._execute(f"SELECT COUNT(*) FROM {table}")
        distinct = self._execute(f"SELECT COUNT(DISTINCT {column}) FROM {table}")
        result = CheckResult(
            check_id=check_id,
            check_name="UNIQUENESS",
            table=table, column=column,
            passed=total == distinct,
            expected=total, actual=distinct,
            details=f"{total - distinct} duplicate(s) detected",
            severity=severity,
        )
        self.results.append(result)
        return result

    # ── Validity ────────────────────────────────────────────────────────────

    def check_value_range(self, check_id: str, table: str, column: str,
                          min_val: float, max_val: float, severity: str = "HIGH") -> CheckResult:
        """Assert all numeric values fall within [min_val, max_val]."""
        out_count = self._execute(
            f"SELECT COUNT(*) FROM {table} "
            f"WHERE {column} < {min_val} OR {column} > {max_val}"
        )
        result = CheckResult(
            check_id=check_id,
            check_name="VALUE RANGE",
            table=table, column=column,
            passed=out_count == 0,
            expected=f"[{min_val}, {max_val}]", actual=f"{out_count} out-of-range",
            details=f"{out_count} value(s) outside [{min_val}, {max_val}]",
            severity=severity,
        )
        self.results.append(result)
        return result

    def check_allowed_values(self, check_id: str, table: str, column: str,
                             allowed: list, severity: str = "HIGH") -> CheckResult:
        """Assert column only contains values from the allowed set."""
        placeholders = ",".join(f"'{v}'" for v in allowed)
        invalid = self._execute(
            f"SELECT COUNT(*) FROM {table} "
            f"WHERE {column} NOT IN ({placeholders}) AND {column} IS NOT NULL"
        )
        result = CheckResult(
            check_id=check_id,
            check_name="ALLOWED VALUES",
            table=table, column=column,
            passed=invalid == 0,
            expected=str(allowed), actual=f"{invalid} invalid value(s)",
            details=f"{invalid} row(s) with unexpected values",
            severity=severity,
        )
        self.results.append(result)
        return result

    def check_regex_pattern(self, check_id: str, table: str, column: str,
                            pattern: str, severity: str = "MEDIUM") -> CheckResult:
        """Assert column values match a LIKE pattern (SQLite compatible)."""
        invalid = self._execute(
            f"SELECT COUNT(*) FROM {table} "
            f"WHERE {column} NOT LIKE '{pattern}' AND {column} IS NOT NULL"
        )
        result = CheckResult(
            check_id=check_id,
            check_name="PATTERN MATCH",
            table=table, column=column,
            passed=invalid == 0,
            expected=f"LIKE '{pattern}'", actual=f"{invalid} non-matching",
            details=f"{invalid} value(s) not matching pattern '{pattern}'",
            severity=severity,
        )
        self.results.append(result)
        return result

    # ── Referential integrity ───────────────────────────────────────────────

    def check_referential_integrity(self, check_id: str,
                                    fact_table: str, fact_col: str,
                                    dim_table: str, dim_col: str,
                                    severity: str = "HIGH") -> CheckResult:
        """Assert no orphan foreign keys."""
        orphans = self._execute(
            f"SELECT COUNT(*) FROM {fact_table} f "
            f"LEFT JOIN {dim_table} d ON f.{fact_col} = d.{dim_col} "
            f"WHERE d.{dim_col} IS NULL AND f.{fact_col} IS NOT NULL"
        )
        result = CheckResult(
            check_id=check_id,
            check_name="REFERENTIAL INTEGRITY",
            table=fact_table, column=fact_col,
            passed=orphans == 0,
            expected=0, actual=orphans,
            details=f"{orphans} orphan row(s): {fact_col} not found in {dim_table}.{dim_col}",
            severity=severity,
        )
        self.results.append(result)
        return result

    # ── Consistency ─────────────────────────────────────────────────────────

    def check_row_count(self, check_id: str, table: str,
                        min_rows: int, max_rows: int = None, severity: str = "HIGH") -> CheckResult:
        """Assert table row count is within expected bounds."""
        count = self._execute(f"SELECT COUNT(*) FROM {table}")
        if max_rows is None:
            passed = count >= min_rows
            expected = f">= {min_rows}"
        else:
            passed = min_rows <= count <= max_rows
            expected = f"[{min_rows}, {max_rows}]"
        result = CheckResult(
            check_id=check_id,
            check_name="ROW COUNT",
            table=table, column=None,
            passed=passed,
            expected=expected, actual=count,
            details=f"Table has {count} row(s)",
            severity=severity,
        )
        self.results.append(result)
        return result

    def check_custom_sql(self, check_id: str, check_name: str, table: str,
                         sql: str, expected_value: Any,
                         severity: str = "MEDIUM") -> CheckResult:
        """Run a custom SQL expression and compare result to expected_value."""
        actual = self._execute(sql)
        result = CheckResult(
            check_id=check_id,
            check_name=f"CUSTOM: {check_name}",
            table=table, column=None,
            passed=actual == expected_value,
            expected=expected_value, actual=actual,
            details=f"SQL: {sql[:80]}",
            severity=severity,
        )
        self.results.append(result)
        return result
