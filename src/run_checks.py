"""
Main entry point — runs all SQL quality checks and generates reports.
"""

import sqlite3
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from checks.sql_checks import SQLQualityChecker
from reporters.quality_reporter import generate_html_report, generate_csv_report

BASE = Path(__file__).resolve().parents[1]
DB_PATH = str(BASE / "data/sql/datamart.db")
REPORT_DIR = str(BASE / "reports")


def setup_database(conn: sqlite3.Connection) -> None:
    """Create and populate the sample DataMart tables."""
    conn.executescript("""
    DROP TABLE IF EXISTS fact_sales;
    DROP TABLE IF EXISTS dim_product;
    DROP TABLE IF EXISTS dim_customer;

    CREATE TABLE dim_customer (
        customer_id TEXT PRIMARY KEY,
        customer_name TEXT NOT NULL,
        country TEXT NOT NULL,
        segment TEXT NOT NULL
    );

    CREATE TABLE dim_product (
        product_id TEXT PRIMARY KEY,
        product_name TEXT NOT NULL,
        category TEXT NOT NULL,
        unit_price REAL NOT NULL
    );

    CREATE TABLE fact_sales (
        sale_id TEXT PRIMARY KEY,
        customer_id TEXT,
        product_id TEXT,
        quantity INTEGER,
        unit_price REAL,
        total_amount REAL,
        sale_date TEXT,
        status TEXT,
        FOREIGN KEY (customer_id) REFERENCES dim_customer(customer_id),
        FOREIGN KEY (product_id)  REFERENCES dim_product(product_id)
    );

    INSERT INTO dim_customer VALUES
      ('C001','Alice Martin','France','Premium'),
      ('C002','Bob Dupont','France','Standard'),
      ('C003','Clara Schmidt','Germany','Premium'),
      ('C004','David Jones','UK','Standard'),
      ('C005','Emma Nguyen','France','Premium');

    INSERT INTO dim_product VALUES
      ('P001','Laptop Pro','Electronics',1200.00),
      ('P002','Wireless Mouse','Electronics',29.99),
      ('P003','Office Chair','Furniture',350.00),
      ('P004','Standing Desk','Furniture',600.00),
      ('P005','Coffee Machine','Appliances',89.99);

    INSERT INTO fact_sales VALUES
      ('S001','C001','P001',1,1200.00,1200.00,'2024-01-05','COMPLETED'),
      ('S002','C002','P002',3,29.99,89.97,'2024-01-06','COMPLETED'),
      ('S003','C001','P003',1,350.00,350.00,'2024-01-07','COMPLETED'),
      ('S004','C003','P001',2,1200.00,2400.00,'2024-01-08','COMPLETED'),
      ('S005','C004','P004',1,600.00,600.00,'2024-01-09','PENDING'),
      ('S006','C005','P005',2,89.99,179.98,'2024-01-10','COMPLETED'),
      ('S007','C002','P003',1,350.00,350.00,'2024-01-11','REFUNDED'),
      ('S008','C003','P002',5,29.99,149.95,'2024-01-12','COMPLETED'),
      ('S009',NULL,'P001',1,1200.00,1200.00,'2024-01-13','COMPLETED'),
      ('S010','C999','P001',1,1200.00,1200.00,'2024-01-14','COMPLETED'),
      ('S011','C001','P002',2,29.99,-59.98,'2024-01-15','COMPLETED'),
      ('S012','C001','P001',1,1200.00,1200.00,'2024-01-05','INVALID_STATUS');
    """)
    conn.commit()


def run_all_checks(conn: sqlite3.Connection) -> SQLQualityChecker:
    checker = SQLQualityChecker(conn)

    # ── dim_customer ────────────────────────────────────────────────────────
    checker.check_not_null("DQ-001", "dim_customer", "customer_id")
    checker.check_not_null("DQ-002", "dim_customer", "customer_name")
    checker.check_uniqueness("DQ-003", "dim_customer", "customer_id")
    checker.check_allowed_values("DQ-004", "dim_customer", "segment",
                                 ["Premium", "Standard"], severity="MEDIUM")
    checker.check_row_count("DQ-005", "dim_customer", min_rows=1)

    # ── dim_product ─────────────────────────────────────────────────────────
    checker.check_not_null("DQ-006", "dim_product", "product_id")
    checker.check_uniqueness("DQ-007", "dim_product", "product_id")
    checker.check_value_range("DQ-008", "dim_product", "unit_price", 0.01, 100000)

    # ── fact_sales ──────────────────────────────────────────────────────────
    checker.check_not_null("DQ-009", "fact_sales", "sale_id")
    checker.check_uniqueness("DQ-010", "fact_sales", "sale_id")
    checker.check_not_null("DQ-011", "fact_sales", "customer_id", severity="HIGH")
    checker.check_referential_integrity("DQ-012", "fact_sales", "customer_id",
                                        "dim_customer", "customer_id")
    checker.check_referential_integrity("DQ-013", "fact_sales", "product_id",
                                        "dim_product", "product_id")
    checker.check_value_range("DQ-014", "fact_sales", "total_amount", 0.01, 1_000_000)
    checker.check_value_range("DQ-015", "fact_sales", "quantity", 1, 10_000)
    checker.check_allowed_values("DQ-016", "fact_sales", "status",
                                 ["COMPLETED", "PENDING", "REFUNDED"])
    checker.check_completeness_rate("DQ-017", "fact_sales", "customer_id",
                                    min_rate=0.95, severity="MEDIUM")
    checker.check_row_count("DQ-018", "fact_sales", min_rows=1)

    # ── Business rule: unit_price × quantity ≈ total_amount ────────────────
    checker.check_custom_sql(
        "DQ-019",
        "Pricing consistency (unit_price * quantity = total_amount)",
        "fact_sales",
        sql="""
            SELECT COUNT(*) FROM fact_sales
            WHERE ABS(unit_price * quantity - total_amount) > 0.01
              AND status != 'REFUNDED'
        """,
        expected_value=0,
        severity="HIGH",
    )

    # ── Date format YYYY-MM-DD ──────────────────────────────────────────────
    checker.check_regex_pattern("DQ-020", "fact_sales", "sale_date",
                                "____-__-__", severity="MEDIUM")

    return checker


if __name__ == "__main__":
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    setup_database(conn)

    checker = run_all_checks(conn)
    conn.close()

    total = len(checker.results)
    passed = sum(1 for r in checker.results if r.passed)
    print(f"\n{'='*50}")
    print(f"Data Quality Report — {passed}/{total} checks passed")
    print(f"{'='*50}\n")
    for r in checker.results:
        icon = "✅" if r.passed else "❌"
        print(f"{icon} [{r.check_id}] {r.check_name} on {r.table}.{r.column or ''} — {r.details}")

    html_path = generate_html_report(
        checker.results,
        os.path.join(REPORT_DIR, "quality_report.html"),
        run_name="DataMart Quality Report — Sprint 01"
    )
    csv_path = generate_csv_report(
        checker.results,
        os.path.join(REPORT_DIR, "quality_report.csv")
    )
    print(f"\n📊 HTML Report: {html_path}")
    print(f"📋 CSV Report:  {csv_path}")

# DQ-021: orders column — no negative quantities
