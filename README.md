# sql-data-validation

At Orange Maroc I spent a lot of time validating data quality manually — checking for nulls, mismatched keys, negative amounts in reports. This project formalizes that into a reusable framework: a set of SQL checks that run against a DataMart and produce an HTML report you can share with the team.

The DataMart here is a classic star schema (customers, products, sales facts) simulated in SQLite. Twenty checks run against it, covering the usual suspects: nulls on mandatory columns, primary key uniqueness, foreign key integrity, value ranges, allowed status values, date formats, and a custom business rule that verifies unit_price * quantity = total_amount. The HTML report shows pass/fail per check with severity labels.

## Structure

```
src/
  checks/
    sql_checks.py          # SQLQualityChecker class — 9 check types
  reporters/
    quality_reporter.py    # generates HTML and CSV from check results
  run_checks.py            # sets up the DB, runs everything, writes reports

tests/
  test_sql_checks.py       # 15 unit tests with in-memory SQLite

data/sql/
  datamart.db              # generated on first run

reports/
  quality_report.html      # the actual deliverable
  quality_report.csv
```

## Running it

```bash
pip install -r requirements.txt
cd src
python run_checks.py
open ../reports/quality_report.html
```

For the tests:

```bash
pytest tests/ -v
```

## The DataMart schema

```
dim_customer  (customer_id PK, customer_name, country, segment)
dim_product   (product_id PK, product_name, category, unit_price)
fact_sales    (sale_id PK, customer_id FK, product_id FK, quantity, unit_price, total_amount, sale_date, status)
```

Four rows in fact_sales have intentional problems: a null customer_id (S009), an orphan foreign key C999 (S010), a negative total_amount (S011), and an invalid status value (S012). All four should show up as failures in the report.

## Check types available

`SQLQualityChecker` exposes these methods — you can use them on any SQLite-compatible connection:

```python
checker.check_not_null(id, table, column)
checker.check_uniqueness(id, table, column)
checker.check_value_range(id, table, column, min, max)
checker.check_allowed_values(id, table, column, allowed_list)
checker.check_referential_integrity(id, fact_table, fk_col, dim_table, pk_col)
checker.check_completeness_rate(id, table, column, min_rate)
checker.check_row_count(id, table, min_rows)
checker.check_regex_pattern(id, table, column, pattern)
checker.check_custom_sql(id, name, table, sql, expected_value)
```

## Stack

Python, SQLite (PostgreSQL-compatible logic), Pytest
