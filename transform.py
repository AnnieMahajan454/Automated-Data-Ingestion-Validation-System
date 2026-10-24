import re
import pandas as pd
import numpy as np
from datetime import datetime
from logger import get_logger, log_file_transformed, log_error

log = get_logger("transform")

FILE_CONFIG = {
    "sales_q1.csv":          {"date_cols": ["Sale Date"],              "numeric_cols": ["Quantity", "Unit Price", "Total"]},
    "sales_q2.csv":          {"date_cols": ["Sale Date"],              "numeric_cols": ["Quantity", "Unit Price", "Total"]},
    "employees.csv":         {"date_cols": ["DATE JOINED"],            "numeric_cols": ["Salary"]},
    "inventory.csv":         {"date_cols": ["Last Restocked"],         "numeric_cols": ["Stock Qty", "Reorder Level", "Unit Cost"]},
    "customer_orders.csv":   {"date_cols": ["Order Date","Delivery Date"], "numeric_cols": ["Amount"]},
    "payroll.csv":           {"date_cols": ["Pay Date"],               "numeric_cols": ["Basic Salary","Bonus","Deductions","Net Pay"]},
    "product_returns.csv":   {"date_cols": ["Return Date"],            "numeric_cols": ["Refund Amount"]},
    "store_branches.csv":    {"date_cols": ["Opening Date"],           "numeric_cols": ["Monthly Target","Actual Sales"]},
    "supplier_invoices.csv": {"date_cols": ["Invoice Date","Due Date"],"numeric_cols": ["Amount","Tax","Total Due"]},
    "website_traffic.csv":   {"date_cols": ["Visit Date"],             "numeric_cols": ["Time Spent (mins)"]},
    "training_records.csv":  {"date_cols": ["Start Date","End Date"],  "numeric_cols": ["Score (%)"]},
    "project_tasks.csv":     {"date_cols": ["Start Date","Deadline"],  "numeric_cols": ["Hours Logged"]},
}

def _to_snake(name):
    name = name.strip().lower().replace(" ", "_")
    name = re.sub(r"[^\w]", "_", name)
    name = re.sub(r"_+", "_", name)
    return name.strip("_")

def drop_duplicates(df, filename):
    before = len(df)
    df = df.drop_duplicates()
    removed = before - len(df)
    if removed:
        log.debug(f"  [{filename}] drop_duplicates: removed {removed} row(s)")
    return df

def standardize_columns(df, filename):
    df.columns = (
        df.columns.str.strip().str.lower()
        .str.replace(" ", "_", regex=False)
        .str.replace(r"[^\w]", "_", regex=True)
        .str.replace(r"_+", "_", regex=True)
        .str.strip("_")
    )
    log.debug(f"  [{filename}] columns standardised: {list(df.columns)}")
    return df

def fix_dates(df, filename, date_cols):
    for col in date_cols:
        col_s = _to_snake(col)
        if col_s not in df.columns:
            continue
        before_nulls = df[col_s].isnull().sum()
        df[col_s] = pd.to_datetime(df[col_s], dayfirst=False, errors="coerce")
        new_nulls = df[col_s].isnull().sum() - before_nulls
        if new_nulls > 0:
            log.debug(f"  [{filename}] '{col_s}' date parse: {new_nulls} value(s) became NaT")
        else:
            log.debug(f"  [{filename}] '{col_s}' → datetime OK")
    return df

def fix_numerics(df, filename, numeric_cols):
    for col in numeric_cols:
        col_s = _to_snake(col)
        if col_s not in df.columns:
            continue
        df[col_s] = df[col_s].replace("N/A", np.nan)
        df[col_s] = pd.to_numeric(df[col_s], errors="coerce")
        nulls = df[col_s].isnull().sum()
        if nulls:
            df[col_s] = df[col_s].fillna(0.0)
            log.debug(f"  [{filename}] '{col_s}' numeric: {nulls} null(s) filled with 0.0")
    return df

def handle_missing(df, filename):
    for col in df.select_dtypes(include="object").columns:
        n = df[col].isnull().sum()
        if n:
            df[col] = df[col].fillna("Unknown")
            log.debug(f"  [{filename}] '{col}': {n} null(s) filled with 'Unknown'")
    return df

def add_loaded_at(df, filename):
    df["loaded_at"] = datetime.now()
    return df

def transform(df, filename):
    config = FILE_CONFIG.get(filename, {"date_cols": [], "numeric_cols": []})
    rows_before = len(df)

    try:
        df = drop_duplicates(df, filename)
        df = standardize_columns(df, filename)
        df = fix_dates(df, filename, config["date_cols"])
        df = fix_numerics(df, filename, config["numeric_cols"])
        df = handle_missing(df, filename)
        df = add_loaded_at(df, filename)

        log_file_transformed(log, filename, rows_before, len(df))
        log.info(f"Transform OK  |  file={filename}  final_shape={df.shape}")
    except Exception as e:
        log_error(log, "transform", filename, str(e))
        raise

    return df

def transform_all(loaded_data):
    cleaned = {}
    log.info(f"Transformation started — {len(loaded_data)} file(s) to process")
    for filename, df in loaded_data.items():
        cleaned[filename] = transform(df.copy(), filename)
    log.info(f"Transformation complete — {len(cleaned)} file(s) cleaned")
    return cleaned

if __name__ == "__main__":
    from pipeline import load_all_csvs
    import warnings; warnings.filterwarnings("ignore")
    raw   = load_all_csvs("data/raw")
    clean = transform_all(raw)
    for name, df in clean.items():
        print(f"  {name}: {df.shape}")
