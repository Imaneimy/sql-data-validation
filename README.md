# SQL Data Validation — Quality Reporting

Data quality validation framework using SQL against a simulated DataMart (dimensions + facts). Runs 20 checks across completeness, uniqueness, referential integrity, value ranges, and business rules. Generates HTML and CSV quality reports automatically.

---

## Project structure

```
03_sql_data_validation/
├── src/
│   ├── checks/
│   │   └── sql_checks.py          # SQLQualityChecker — 9 check types
│   ├── reporters/
│   │   └── quality_reporter.py    # HTML + CSV report generation
│   └── run_checks.py              # Entry point — runs all checks
├── tests/
│   └── test_sql_checks.py         # TC-SQL-001 to TC-SQL-015
├── data/sql/
│   └── datamart.db                # SQLite database (generated on run)
└── reports/
    ├── quality_report.html        # Visual report (generated)
    └── quality_report.csv         # CSV export (generated)
```

---

## Setup

```bash
pip install -r requirements.txt

# Run all checks and generate reports
cd src
python run_checks.py

# Open the HTML report
open ../reports/quality_report.html

# Run unit tests
pytest tests/ -v
```

---

## Check types

| Check | IDs | Description |
|-------|-----|-------------|
| NOT NULL | DQ-001, 002, 009, 011 | Mandatory columns with no NULL values |
| UNIQUENESS | DQ-003, 007, 010 | Primary key uniqueness |
| VALUE RANGE | DQ-008, 014, 015 | Positive amounts and quantities |
| ALLOWED VALUES | DQ-004, 016 | Values from a defined reference set |
| REFERENTIAL INTEGRITY | DQ-012, 013 | Foreign keys exist in dimension tables |
| COMPLETENESS RATE | DQ-017 | Non-null rate >= 95% |
| ROW COUNT | DQ-005, 018 | Minimum row count threshold |
| CUSTOM SQL | DQ-019 | unit_price x quantity = total_amount |
| PATTERN MATCH | DQ-020 | Date format YYYY-MM-DD |

---

## DataMart schema

```
dim_customer (customer_id, customer_name, country, segment)
dim_product  (product_id, product_name, category, unit_price)
fact_sales   (sale_id, customer_id, product_id, quantity, unit_price, total_amount, sale_date, status)
```

---

## Intentional anomalies in test data

| Row | Anomaly | Check triggered |
|-----|---------|-----------------|
| S009 | NULL customer_id | DQ-011 |
| S010 | Orphan FK C999 | DQ-012 |
| S011 | total_amount = -59.98 | DQ-014 |
| S012 | status = INVALID_STATUS | DQ-016 |

---

## Stack

Python / SQLite (compatible PostgreSQL) / Pytest

---

## Author

Imane Moussafir — Data & BI Engineer
