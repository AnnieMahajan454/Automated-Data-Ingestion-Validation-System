"""
run_pipeline.py  —  Master Orchestrator (with full logging)
"""
import time
import warnings
from datetime import datetime

warnings.filterwarnings("ignore")

from logger import (
    get_logger, log_run_start, log_run_end,
    log_stage_start, log_stage_end
)
from pipeline  import load_all_csvs
from transform import transform_all
from loader    import get_engine, create_log_table, load_all, verify_load

log = get_logger("run_pipeline")
RAW_FOLDER = "data/raw"

def elapsed(start):
    return f"{time.time() - start:.2f}s"

def run_pipeline():
    pipeline_start = time.time()
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    log_run_start(log, run_id)

    results = {
        "run_id":        run_id,
        "run_timestamp": run_ts,
        "files_found":   0,
        "files_loaded":  0,
        "files_skipped": 0,
        "rows_inserted": 0,
        "errors":        [],
        "status":        "pending",
    }

    # ── Stage 1: Ingest ───────────────────────────────────────
    log_stage_start(log, "INGEST")
    t = time.time()
    try:
        raw_data = load_all_csvs(RAW_FOLDER)
        results["files_found"] = len(raw_data)
        log_stage_end(log, "INGEST", elapsed(t))
    except Exception as e:
        log.error(f"INGEST stage failed: {e}")
        results["errors"].append(str(e))
        results["status"] = "failed"
        log_run_end(log, run_id, "failed", elapsed(pipeline_start))
        return results

    if not raw_data:
        log.warning("No CSV files found — pipeline halted")
        results["status"] = "no_files"
        log_run_end(log, run_id, "no_files", elapsed(pipeline_start))
        return results

    # ── Stage 2: Transform ────────────────────────────────────
    log_stage_start(log, "TRANSFORM")
    t = time.time()
    try:
        clean_data = transform_all(raw_data)
        log_stage_end(log, "TRANSFORM", elapsed(t))
    except Exception as e:
        log.error(f"TRANSFORM stage failed: {e}")
        results["errors"].append(str(e))
        results["status"] = "failed"
        log_run_end(log, run_id, "failed", elapsed(pipeline_start))
        return results

    # ── Stage 3: Load ─────────────────────────────────────────
    log_stage_start(log, "LOAD")
    t = time.time()
    try:
        engine = get_engine()
        create_log_table(engine)
        summary = load_all(engine, clean_data)
        results["files_loaded"]  = summary["loaded"]
        results["files_skipped"] = summary["skipped"]
        results["rows_inserted"] = summary["rows"]
        log_stage_end(log, "LOAD", elapsed(t))
    except Exception as e:
        log.error(f"LOAD stage failed: {e}")
        results["errors"].append(str(e))
        results["status"] = "failed"
        log_run_end(log, run_id, "failed", elapsed(pipeline_start))
        return results

    # ── Stage 4: Verify ───────────────────────────────────────
    log_stage_start(log, "VERIFY")
    t = time.time()
    verify_load(engine)
    log_stage_end(log, "VERIFY", elapsed(t))

    # ── Final ─────────────────────────────────────────────────
    results["status"] = "success"
    log.info(
        f"SUMMARY  |  files_found={results['files_found']}  "
        f"files_loaded={results['files_loaded']}  "
        f"files_skipped={results['files_skipped']}  "
        f"rows_inserted={results['rows_inserted']}"
    )
    log_run_end(log, run_id, "success", elapsed(pipeline_start))
    return results

if __name__ == "__main__":
    run_pipeline()
