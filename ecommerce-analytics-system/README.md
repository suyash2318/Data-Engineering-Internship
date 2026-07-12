# E-Commerce Analytics System

A simple, end-to-end data pipeline built to load, clean, and analyze transactional e-commerce data. 

This project was built to practice designing structured database schemas, implementing data cleaning workflows in Python, and writing analytic SQL queries (including window functions, CTEs, and cohort analysis).

---

## Why This Was Built
In e-commerce, raw transaction logs are often messy. They contain inconsistent date formats, missing fields, customer typos, and double-posted entries. This project simulates a real-world scenario where data must be extracted from raw CSVs, cleaned via Python (Pandas), loaded into a relational database (SQLite) with strict integrity rules, and queried to produce business insights.

---

## Design Decisions
- **SQLite**: Chose SQLite because it requires zero configuration or external database servers to run. It stores the database in a single file (`ecommerce.db`), which makes it perfect for local development and testing.
- **Pandas for Cleaning**: Used Pandas to handle the initial data cleaning phase. Its vectorization makes operations like email format verification and string stripping quick and easy to write.
- **Python Standard Library CLI**: The reporting tool (`report_cli.py`) uses only Python's standard library. Avoiding external dependencies (like `tabulate`) makes the tool portable and simple to run on any machine.
- **Database Indexing**: Added indexes on commonly queried columns (e.g. `order_date`, `status`, `customer_id`, `category`) to ensure aggregations and joins stay fast as the dataset grows.

---

## Challenges Encountered
1. **SQLite Date Processing**: SQLite doesn't have a native DATETIME type, so dates are stored as text. Parsing and formatting mixed-format dates (e.g., swapping between `YYYY-MM-DD` and `DD-MM-YYYY` formats) in Python before inserting them into SQLite was critical to make time-based queries work.
2. **Referential Integrity**: Raw transaction items can sometimes reference non-existent orders. Had to build check routines in Python to identify and remove these orphan order items before inserting them into the database to satisfy the Foreign Key constraints.
3. **Handling Returns**: Transactions with negative quantities represent returns. Calculating net revenue correctly required filtering these out of normal sales metrics but retaining them for return-rate queries.

---

## Future Improvements
- **Automated Airflow/Prefect DAG**: Transition the raw-to-db pipeline into a proper scheduler/orchestrator rather than running scripts manually.
- **Incremental Loads**: Currently, the pipeline rebuilds the database from scratch. I'd like to implement upsert logic to support incremental data updates.
- **Dashboarding**: Build a simple Streamlit dashboard to replace the text-based CLI.

---

## Git Commit History (Suggested Timeline)
Here is a realistic timeline of how this project was iteratively developed:
1. `feat: initial schema setup and database initialization script`
2. `feat: add synthetic data generator with intentional data quality issues`
3. `feat: implement clean_data.py to normalize dates, emails, and load SQLite`
4. `fix: add referential integrity checks and clean orphaned order items`
5. `feat: add basic and intermediate SQL aggregation queries`
6. `feat: implement advanced window functions, cohort retention, and purchase pairs`
7. `feat: build report_cli.py with stdlib-only formatting for monthly/weekly summaries`
8. `test: add edge-case test suite for check constraints and capping rules`
9. `docs: update README with design decisions, challenges, and timeline`

---

## Quick Start

### 1. Prerequisites
Install dependencies:
```bash
pip install faker pandas
```

### 2. Generate Data
Generate synthetic raw CSVs with quality anomalies:
```bash
python scripts/generate_data.py
```

### 3. Run Cleaning & Loading
Clean the raw CSVs, export clean files to `data/cleaned/`, and load them into `ecommerce.db`:
```bash
python scripts/clean_data.py
```

### 4. Run Queries
Run basic, intermediate, and advanced queries against the SQLite database:
```bash
# Basic aggregation queries (e.g., category revenue, top 10 customers)
sqlite3 ecommerce.db < sql/aggregations.sql

# Intermediate queries (e.g., return rates, products with high return rates)
sqlite3 ecommerce.db < sql/intermediate.sql

# Advanced queries (e.g., rolling totals, cohort retention, bought-together pairs)
sqlite3 ecommerce.db < sql/window_functions.sql

# Cohort and customer lifecycle metrics
sqlite3 ecommerce.db < sql/cohort_analysis.sql
```

### 5. Generate CLI Reports
Generate text summary reports over a date range:
```bash
# Monthly overview
python scripts/report_cli.py --type monthly --start 2023-01-01 --end 2025-12-31

# Daily report for a specific month
python scripts/report_cli.py --type daily --start 2025-11-01 --end 2025-11-30
```

### 6. Run Tests
Verify system integrity constraints:
```bash
python scripts/test_edge_cases.py
```
