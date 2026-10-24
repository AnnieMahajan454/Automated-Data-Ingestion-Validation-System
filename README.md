# CSV to SQL Weekly Pipeline

A production-ready data engineering pipeline that **automatically ingests, cleans, and loads CSV files into a SQL database** — every week, without manual effort.

Built with Python, pandas, and SQLAlchemy. No cloud account needed. Runs entirely on your local machine.

---

## What It Does

```
data/raw/*.csv  →  Ingest  →  Transform  →  Load  →  pipeline.db
                   (scan)      (clean)       (SQL)     (SQLite)
```

Every week the pipeline:
1. Scans a folder for new CSV files
2. Cleans the data (drops duplicates, fixes types, fills nulls)
3. Loads clean rows into a SQL database
4. Skips files it has already loaded (duplicate-safe)
5. Logs everything to `pipeline.log` for auditability

---

## Project Structure

```
csv_pipeline/
│
├── data/
│   └── raw/                  ← drop your weekly CSVs here
│
├── pipeline.py               ← Stage 1: Scan & ingest CSVs
├── transform.py              ← Stage 2: Clean & transform data
├── loader.py                 ← Stage 3: Load into SQL database
├── run_pipeline.py           ← Master orchestrator (run this)
├── scheduler.py              ← Automated weekly trigger
├── logger.py                 ← Centralised logging module
├── test_pipeline.py          ← Full pipeline test suite
│
├── pipeline.db               ← SQLite database (auto-created)
├── pipeline.log              ← Audit log (auto-created)
└── scheduler.log             ← Scheduler history (auto-created)
```

---

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/csv-to-sql-pipeline.git
cd csv-to-sql-pipeline
```

### 2. Install dependencies

```bash
pip install pandas sqlalchemy psycopg2-binary schedule
```

### 3. Drop your CSV files in

```bash
# Copy your CSV files into the raw folder
cp your_data.csv data/raw/
```

### 4. Run the pipeline

```bash
python run_pipeline.py
```

That's it. The database and log file are created automatically on first run.

---

## Running the Scheduler

**Test mode** — fires every minute so you can confirm it works:
```bash
python scheduler.py --test
```

**Weekly mode** — fires every Monday at 08:00 automatically:
```bash
python scheduler.py
```

Stop at any time with `Ctrl + C`.

---

## Running the Tests

```bash
python test_pipeline.py
```

The test suite:
- Drops a new CSV and confirms it loads correctly
- Queries the database to verify data landed
- Drops the same CSV again and confirms it is **not** loaded twice
- Runs integrity checks across all tables

---

## Database

The pipeline uses **SQLite** by default — no server needed, zero setup.

The database file `pipeline.db` is created automatically in the project root.

**To switch to PostgreSQL**, change one line in `loader.py`:

```python
# SQLite (default)
DB_URL = "sqlite:///pipeline.db"

# PostgreSQL
DB_URL = "postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/csv_pipeline"
```

Nothing else needs to change.

---

## SQL Tables Created

| Table | Source File | Description |
|---|---|---|
| `sales` | `sales_q1.csv`, `sales_q2.csv` | Weekly sales transactions |
| `employees` | `employees.csv` | Employee records |
| `inventory` | `inventory.csv` | Product stock levels |
| `customer_orders` | `customer_orders.csv` | Customer order history |
| `payroll` | `payroll.csv` | Monthly payroll data |
| `product_returns` | `product_returns.csv` | Return and refund records |
| `store_branches` | `store_branches.csv` | Branch performance |
| `supplier_invoices` | `supplier_invoices.csv` | Supplier billing |
| `website_traffic` | `website_traffic.csv` | Web analytics |
| `training_records` | `training_records.csv` | Staff training history |
| `project_tasks` | `project_tasks.csv` | Task management |
| `pipeline_load_log` | *(auto)* | Tracks which files have been loaded |

---

## Transformations Applied

Every CSV goes through these cleaning steps before loading:

| Step | What It Does |
|---|---|
| Drop duplicates | Removes exact duplicate rows |
| Standardise columns | `Customer Name` → `customer_name` |
| Fix date formats | Handles `2024-01-05`, `01/05/2024`, `Jan 5 2024` |
| Fix numerics | Converts `N/A` and blank cells to `0.0` |
| Fill missing text | Blank text fields → `"Unknown"` |
| Add `loaded_at` | Timestamps every row on ingestion |

---

## Logging

All pipeline activity is written to two places simultaneously:

- **Terminal** — colour-coded by log level
- **`pipeline.log`** — plain-text permanent record

```
2024-06-10 08:00:01  INFO  [pipeline]   INGESTED  | file=sales_q2.csv  rows=250  cols=8
2024-06-10 08:00:02  INFO  [transform]  TRANSFORMED | file=sales_q2.csv  rows_before=250  rows_after=247  duplicates_removed=3
2024-06-10 08:00:02  INFO  [loader]     LOADED  | file=sales_q2.csv  table=sales  rows_inserted=247
2024-06-10 08:00:02  INFO  [run_pipeline] PIPELINE RUN FINISHED | status=success  time=1.04s
```

---

## Adding a New Weekly File

1. Drop the new CSV into `data/raw/`
2. Add one line to `FILE_TO_TABLE` in `loader.py`:

```python
FILE_TO_TABLE = {
    ...
    "sales_q3.csv": "sales",   # ← new file maps to existing table
}
```

3. Add the same entry to `FILE_CONFIG` in `transform.py` if it has date or numeric columns.

The next pipeline run picks it up automatically.

---

## Tech Stack

| Tool | Purpose | Cost |
|---|---|---|
| Python 3.x | Core language | Free |
| pandas | CSV reading & transformation | Free |
| SQLAlchemy | Database connection layer | Free |
| SQLite | Local SQL database | Free (built into Python) |
| PostgreSQL | Production-grade database (optional) | Free |
| schedule | Weekly automation | Free |
