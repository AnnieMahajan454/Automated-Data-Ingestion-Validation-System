import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime
from logger import get_logger, log_file_loaded, log_file_skipped_load, log_error

log = get_logger("loader")

DB_URL    = "sqlite:///pipeline.db"
LOG_TABLE = "pipeline_load_log"

FILE_TO_TABLE = {
    "sales_q1.csv":          "sales",
    "sales_q2.csv":          "sales",
    "employees.csv":         "employees",
    "inventory.csv":         "inventory",
    "customer_orders.csv":   "customer_orders",
    "payroll.csv":           "payroll",
    "product_returns.csv":   "product_returns",
    "store_branches.csv":    "store_branches",
    "supplier_invoices.csv": "supplier_invoices",
    "website_traffic.csv":   "website_traffic",
    "training_records.csv":  "training_records",
    "project_tasks.csv":     "project_tasks",
}

def get_engine():
    engine = create_engine(DB_URL)
    log.info(f"DB connection established: {DB_URL}")
    return engine

def create_log_table(engine):
    sql = f"""
        CREATE TABLE IF NOT EXISTS {LOG_TABLE} (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            filename     TEXT    NOT NULL,
            table_name   TEXT    NOT NULL,
            rows_loaded  INTEGER NOT NULL,
            loaded_at    TEXT    NOT NULL
        )
    """
    with engine.connect() as conn:
        conn.execute(text(sql))
        conn.commit()
    log.debug(f"Log table '{LOG_TABLE}' ready")

def already_loaded(engine, filename):
    with engine.connect() as conn:
        result = conn.execute(
            text(f"SELECT COUNT(*) FROM {LOG_TABLE} WHERE filename = :f"),
            {"f": filename}
        )
        return result.scalar() > 0

def log_load(engine, filename, table_name, rows_loaded):
    with engine.connect() as conn:
        conn.execute(text(
            f"INSERT INTO {LOG_TABLE} (filename, table_name, rows_loaded, loaded_at) "
            f"VALUES (:filename, :table_name, :rows_loaded, :loaded_at)"
        ), {
            "filename":    filename,
            "table_name":  table_name,
            "rows_loaded": rows_loaded,
            "loaded_at":   datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })
        conn.commit()

def load_dataframe(engine, df, table_name, filename):
    try:
        df.to_sql(name=table_name, con=engine, if_exists="append", index=False)
        log_load(engine, filename, table_name, len(df))
        log_file_loaded(log, filename, table_name, len(df))
        return len(df)
    except Exception as e:
        log_error(log, "load", filename, str(e))
        return 0

def load_all(engine, cleaned_data):
    total_rows = loaded_count = skipped_count = 0
    log.info(f"Load layer started — {len(cleaned_data)} file(s) to process")

    for filename, df in cleaned_data.items():
        table_name = FILE_TO_TABLE.get(filename)
        if not table_name:
            log.warning(f"No table mapping for '{filename}' — skipping")
            skipped_count += 1
            continue

        if already_loaded(engine, filename):
            log_file_skipped_load(log, filename, "already loaded in a previous run")
            skipped_count += 1
            continue

        rows = load_dataframe(engine, df, table_name, filename)
        total_rows   += rows
        loaded_count += 1

    log.info(
        f"Load complete — files_loaded={loaded_count}  "
        f"files_skipped={skipped_count}  total_rows_inserted={total_rows}"
    )
    return {"loaded": loaded_count, "skipped": skipped_count, "rows": total_rows}

def verify_load(engine):
    log.info("Verification: querying row counts")
    with engine.connect() as conn:
        for filename, table_name in FILE_TO_TABLE.items():
            try:
                count = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
                log.info(f"  Table '{table_name}': {count} row(s)")
            except Exception:
                log.warning(f"  Table '{table_name}': not found")
