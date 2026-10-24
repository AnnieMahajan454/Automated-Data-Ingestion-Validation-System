"""
test_pipeline.py  —  Full Pipeline Test Suite
══════════════════════════════════════════════
Runs 4 tests exactly as described in Step 8:

  TEST 1 — Drop a NEW CSV into data/raw/ and run the pipeline
  TEST 2 — Open the SQL database and confirm data landed
  TEST 3 — Drop the SAME CSV again and confirm it is NOT loaded twice
  TEST 4 — Final integrity check across all tables

Run with:
    python test_pipeline.py
"""

import os
import shutil
import sqlite3
import warnings
import pandas as pd
from datetime import datetime

warnings.filterwarnings("ignore")

# ── Import pipeline layers ────────────────────────────────────
from run_pipeline import run_pipeline
from loader import DB_URL

# ── SQLite file path (strip the sqlite:/// prefix) ───────────
DB_PATH = DB_URL.replace("sqlite:///", "")


# ═════════════════════════════════════════════════════════════
#  HELPERS
# ═════════════════════════════════════════════════════════════
def section(title, icon="🔷"):
    print(f"\n{'━'*57}")
    print(f"  {icon}  {title}")
    print(f"{'━'*57}")

def pass_fail(condition, msg_pass, msg_fail):
    if condition:
        print(f"  ✅  PASS  —  {msg_pass}")
    else:
        print(f"  ❌  FAIL  —  {msg_fail}")
    return condition

def db_query(sql, params=None):
    """Run a SQL query against pipeline.db and return all rows."""
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cur.execute(sql, params or [])
    rows = cur.fetchall()
    conn.close()
    return rows

def get_table_count(table):
    """Return the row count for a given SQL table."""
    rows = db_query(f"SELECT COUNT(*) FROM {table}")
    return rows[0][0]

def get_log_entries(filename):
    """Return all log entries for a given filename."""
    return db_query(
        "SELECT filename, table_name, rows_loaded, loaded_at "
        "FROM pipeline_load_log WHERE filename = ?",
        [filename]
    )


# ═════════════════════════════════════════════════════════════
#  NEW CSV — create a fresh weekly CSV to drop in
# ═════════════════════════════════════════════════════════════
NEW_CSV_NAME = "sales_q2.csv"
NEW_CSV_PATH = f"data/raw/{NEW_CSV_NAME}"
NEW_TABLE    = "sales"     # same table as sales_q1 — appends to it

NEW_CSV_CONTENT = """Order ID,Customer Name,Sale Date,Product,Quantity,Unit Price,Total,Region
2001,Linda Carter,2024-04-02,Laptop,1,850.00,850.00,North
2002,peter parker,04/05/2024,Mouse,3,25.50,76.50,South
2003,TONY STARK,2024-04-08,Monitor,2,200.00,400.00,East
2004,Bruce Wayne,April 10 2024,Keyboard,,45.00,90.00,West
2005,Diana Prince,2024-04-12,USB Hub,4,15.00,60.00,North
2006,clark kent,2024/04/15,Headphones,1,120.00,120.00,
2007,,2024-04-18,Webcam,2,89.99,179.98,South
2008,Barry Allen,18-04-2024,Laptop,1,850.00,850.00,East
2003,TONY STARK,2024-04-08,Monitor,2,200.00,400.00,East
2009,Hal Jordan,2024-04-22,Mouse,N/A,25.50,,West
2010,Arthur Curry,2024-04-25,Laptop Stand,3,22.00,66.00,North
"""


# ═════════════════════════════════════════════════════════════
#  TEST 1 — Drop a NEW CSV and run the pipeline
# ═════════════════════════════════════════════════════════════
def test_1_new_csv():
    section("TEST 1 — Drop a new CSV into data/raw/ and run pipeline", "📥")

    # ── Record row count BEFORE the run ──────────────────────
    rows_before = get_table_count(NEW_TABLE)
    log_before  = len(get_log_entries(NEW_CSV_NAME))

    print(f"\n  📊 State BEFORE run:")
    print(f"     '{NEW_TABLE}' table row count : {rows_before}")
    print(f"     Log entries for {NEW_CSV_NAME}: {log_before}")

    # ── Write the new CSV to data/raw/ ───────────────────────
    with open(NEW_CSV_PATH, "w") as f:
        f.write(NEW_CSV_CONTENT)
    print(f"\n  📄 Dropped '{NEW_CSV_NAME}' into data/raw/")
    print(f"     (11 raw rows, includes 1 duplicate + messy data)")

    # ── Run the full pipeline ─────────────────────────────────
    print(f"\n  🚀 Running pipeline...\n")
    result = run_pipeline()

    # ── Record row count AFTER the run ───────────────────────
    rows_after = get_table_count(NEW_TABLE)
    log_after  = len(get_log_entries(NEW_CSV_NAME))
    new_rows   = rows_after - rows_before

    print(f"\n  📊 State AFTER run:")
    print(f"     '{NEW_TABLE}' table row count : {rows_after}  (+{new_rows} new rows)")
    print(f"     Log entries for {NEW_CSV_NAME}: {log_after}")

    # ── Assertions ────────────────────────────────────────────
    print(f"\n  🧪 Test Results:")
    r1 = pass_fail(result["status"] == "success",
                   "Pipeline returned status=success",
                   f"Pipeline status was '{result['status']}'")
    r2 = pass_fail(new_rows == 10,
                   f"10 clean rows inserted (1 duplicate removed by transform)",
                   f"Expected 10 new rows, got {new_rows}")
    r3 = pass_fail(log_after == 1,
                   f"'{NEW_CSV_NAME}' logged exactly once in pipeline_load_log",
                   f"Expected 1 log entry, found {log_after}")
    r4 = pass_fail(result["files_loaded"] == 1,
                   "Only the new file was loaded (existing 11 correctly skipped)",
                   f"Expected 1 file loaded, got {result['files_loaded']}")

    return all([r1, r2, r3, r4])


# ═════════════════════════════════════════════════════════════
#  TEST 2 — Open SQL database and confirm data landed correctly
# ═════════════════════════════════════════════════════════════
def test_2_verify_sql():
    section("TEST 2 — Open SQL database & confirm data landed", "🗄️")

    # ── Row counts for every table ────────────────────────────
    print(f"\n  📋 Row counts across all tables in pipeline.db:\n")

    tables = [
        "sales", "employees", "inventory", "customer_orders",
        "payroll", "product_returns", "store_branches",
        "supplier_invoices", "website_traffic", "training_records",
        "project_tasks"
    ]

    all_present = True
    for table in tables:
        try:
            count = get_table_count(table)
            marker = "✅" if count > 0 else "⚠️ "
            print(f"     {marker}  {table:<25} →  {count:>3} row(s)")
            if count == 0:
                all_present = False
        except Exception as e:
            print(f"     ❌  {table:<25} →  ERROR: {e}")
            all_present = False

    # ── Preview first 5 rows of the NEW data ─────────────────
    print(f"\n  👁  Preview — first 5 rows of new data in '{NEW_TABLE}':\n")
    conn = sqlite3.connect(DB_PATH)
    df   = pd.read_sql(
        f"SELECT * FROM {NEW_TABLE} ORDER BY rowid DESC LIMIT 5",
        conn
    )
    conn.close()

    # Only show key columns for readability
    preview_cols = ["order_id", "customer_name", "sale_date",
                    "product", "quantity", "total", "region", "loaded_at"]
    available = [c for c in preview_cols if c in df.columns]
    print(df[available].to_string(index=False))

    # ── Check the load log table ──────────────────────────────
    print(f"\n  📋 Full pipeline_load_log:\n")
    log_rows = db_query(
        "SELECT filename, table_name, rows_loaded, loaded_at "
        "FROM pipeline_load_log ORDER BY id"
    )
    print(f"     {'Filename':<30} {'Table':<22} {'Rows':>5}  Loaded At")
    print(f"     {'─'*75}")
    for row in log_rows:
        print(f"     {row[0]:<30} {row[1]:<22} {row[2]:>5}  {row[3]}")

    print(f"\n  🧪 Test Results:")
    r1 = pass_fail(all_present,
                   "All 11 tables exist and have data",
                   "One or more tables are empty or missing")
    r2 = pass_fail(len(log_rows) == 12,
                   "Load log has exactly 12 entries (11 original + 1 new)",
                   f"Expected 12 log entries, found {len(log_rows)}")

    return all([r1, r2])


# ═════════════════════════════════════════════════════════════
#  TEST 3 — Drop the SAME CSV again, confirm NOT loaded twice
# ═════════════════════════════════════════════════════════════
def test_3_no_duplicate_load():
    section("TEST 3 — Drop the SAME CSV again — must NOT load twice", "🔁")

    rows_before = get_table_count(NEW_TABLE)
    log_before  = len(get_log_entries(NEW_CSV_NAME))

    print(f"\n  📊 State BEFORE second run:")
    print(f"     '{NEW_TABLE}' row count    : {rows_before}")
    print(f"     Log entries for new file  : {log_before}")

    # The file is still in data/raw/ — pipeline runs again
    print(f"\n  ♻️  File '{NEW_CSV_NAME}' is still in data/raw/")
    print(f"     Running pipeline again...\n")

    result = run_pipeline()

    rows_after = get_table_count(NEW_TABLE)
    log_after  = len(get_log_entries(NEW_CSV_NAME))

    print(f"\n  📊 State AFTER second run:")
    print(f"     '{NEW_TABLE}' row count    : {rows_after}  (should be unchanged)")
    print(f"     Log entries for new file  : {log_after}  (should still be 1)")

    print(f"\n  🧪 Test Results:")
    r1 = pass_fail(rows_after == rows_before,
                   f"Row count unchanged at {rows_after} — duplicate blocked ✋",
                   f"Row count grew from {rows_before} to {rows_after} — DUPLICATE INSERTED!")
    r2 = pass_fail(log_after == 1,
                   "Log still shows exactly 1 entry for this file",
                   f"Log now has {log_after} entries — should be 1")
    r3 = pass_fail(result["files_skipped"] >= 1,
                   f"{result['files_skipped']} file(s) correctly skipped this run",
                   "No files were skipped — duplicate protection may have failed")

    return all([r1, r2, r3])


# ═════════════════════════════════════════════════════════════
#  TEST 4 — Final integrity check
# ═════════════════════════════════════════════════════════════
def test_4_integrity():
    section("TEST 4 — Final integrity check across all tables", "🔬")

    print(f"\n  Running integrity checks...\n")
    passed = []

    # Check 1: All 12 files in the log
    log_count = db_query("SELECT COUNT(*) FROM pipeline_load_log")[0][0]
    passed.append(pass_fail(log_count == 12,
        f"pipeline_load_log has 12 entries (11 original + 1 new)",
        f"pipeline_load_log has {log_count} entries (expected 12)"))

    # Check 2: Sales table has 20 rows (10 from q1 + 10 from q2)
    sales_count = get_table_count("sales")
    passed.append(pass_fail(sales_count == 20,
        f"'sales' table has 20 rows (10 from sales_q1 + 10 from sales_q2)",
        f"'sales' table has {sales_count} rows (expected 20)"))

    # Check 3: loaded_at column exists and has values in new data
    rows = db_query("SELECT COUNT(*) FROM sales WHERE loaded_at IS NOT NULL")
    has_ts = rows[0][0] == 20
    passed.append(pass_fail(has_ts,
        "All 20 sales rows have a loaded_at timestamp",
        f"Some rows are missing loaded_at timestamp"))

    # Check 4: No completely empty tables
    tables = ["employees", "inventory", "customer_orders", "payroll",
              "product_returns", "store_branches", "supplier_invoices",
              "website_traffic", "training_records", "project_tasks"]
    empty = [t for t in tables if get_table_count(t) == 0]
    passed.append(pass_fail(len(empty) == 0,
        "All 11 tables have data (none empty)",
        f"Empty tables found: {empty}"))

    # Check 5: Confirm no raw 'N/A' strings leaked into the sales table
    na_rows = db_query("SELECT COUNT(*) FROM sales WHERE quantity = 'N/A'")[0][0]
    passed.append(pass_fail(na_rows == 0,
        "'N/A' strings were correctly converted to 0.0 in sales.quantity",
        f"{na_rows} raw 'N/A' strings found in sales.quantity — transform may have failed"))

    return all(passed)


# ═════════════════════════════════════════════════════════════
#  MAIN — run all 4 tests and print final scorecard
# ═════════════════════════════════════════════════════════════
def main():
    print("\n")
    print("╔" + "═"*55 + "╗")
    print("║       🧪  PIPELINE TEST SUITE  —  STARTING          ║")
    print(f"║       🕐  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                       ║")
    print("╚" + "═"*55 + "╝")

    results = {}

    results["TEST 1: New CSV loads correctly"]         = test_1_new_csv()
    results["TEST 2: SQL data confirmed correct"]      = test_2_verify_sql()
    results["TEST 3: Same CSV not loaded twice"]       = test_3_no_duplicate_load()
    results["TEST 4: Final integrity check"]           = test_4_integrity()

    # ── Scorecard ─────────────────────────────────────────────
    section("TEST SCORECARD", "📊")
    print()
    total  = len(results)
    passed = sum(results.values())

    for name, result in results.items():
        icon = "✅ PASS" if result else "❌ FAIL"
        print(f"  {icon}  {name}")

    print(f"\n{'━'*57}")
    print(f"  Result: {passed}/{total} tests passed")

    if passed == total:
        print(f"  🎉  ALL TESTS PASSED — pipeline is working correctly!")
    else:
        failed = total - passed
        print(f"  ⚠️   {failed} test(s) failed — review output above")
    print(f"{'━'*57}\n")


if __name__ == "__main__":
    main()
