"""
logger.py  —  Centralised Logging Module
═════════════════════════════════════════
One import in every other file gives the entire pipeline
a consistent, structured audit trail.

Usage in any file:
    from logger import get_logger
    log = get_logger(__name__)
    log.info("Something happened")
    log.warning("Something looks off")
    log.error("Something broke")

Log output goes to TWO places simultaneously:
  • terminal  (coloured, human-readable)
  • pipeline.log  (plain text, permanent record)
"""

import logging
import os
import sys
from datetime import datetime

# ─────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────
LOG_FILE  = "pipeline.log"   # file written in the project root
LOG_LEVEL = logging.DEBUG    # capture everything DEBUG and above


# ═════════════════════════════════════════════════════════════
#  CUSTOM FORMATTER  —  coloured terminal output
# ═════════════════════════════════════════════════════════════
class ColouredFormatter(logging.Formatter):
    """
    Adds ANSI colour codes to terminal log lines by level:
      DEBUG   → grey
      INFO    → white
      WARNING → yellow
      ERROR   → red
      CRITICAL→ bold red
    The log FILE always gets plain text (no colour codes).
    """

    GREY    = "\033[38;5;245m"
    WHITE   = "\033[97m"
    YELLOW  = "\033[93m"
    RED     = "\033[91m"
    BOLD_RED= "\033[1;91m"
    RESET   = "\033[0m"

    LEVEL_COLOURS = {
        logging.DEBUG:    GREY,
        logging.INFO:     WHITE,
        logging.WARNING:  YELLOW,
        logging.ERROR:    RED,
        logging.CRITICAL: BOLD_RED,
    }

    FMT = "%(asctime)s  %(levelname)-8s  [%(name)s]  %(message)s"
    DATE_FMT = "%Y-%m-%d %H:%M:%S"

    def format(self, record):
        colour = self.LEVEL_COLOURS.get(record.levelno, self.WHITE)
        formatter = logging.Formatter(
            fmt     = colour + self.FMT + self.RESET,
            datefmt = self.DATE_FMT
        )
        return formatter.format(record)


# ═════════════════════════════════════════════════════════════
#  PLAIN FORMATTER  —  for the log file (no colour codes)
# ═════════════════════════════════════════════════════════════
PLAIN_FMT  = "%(asctime)s  %(levelname)-8s  [%(name)s]  %(message)s"
DATE_FMT   = "%Y-%m-%d %H:%M:%S"


# ═════════════════════════════════════════════════════════════
#  SETUP FUNCTION  —  call once at startup
# ═════════════════════════════════════════════════════════════
def setup_logging():
    """
    Configures the root logger with two handlers:
      1. StreamHandler  → coloured output to terminal
      2. FileHandler    → plain text appended to pipeline.log

    Called automatically when logger.py is first imported.
    Safe to call multiple times (handlers won't duplicate).
    """
    root = logging.getLogger()

    # Avoid adding duplicate handlers if already configured
    if root.handlers:
        return

    root.setLevel(LOG_LEVEL)

    # ── Handler 1: Terminal (coloured) ────────────────────────
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(LOG_LEVEL)
    console_handler.setFormatter(ColouredFormatter())

    # ── Handler 2: File (plain text) ─────────────────────────
    file_handler = logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8")
    file_handler.setLevel(LOG_LEVEL)
    file_handler.setFormatter(
        logging.Formatter(fmt=PLAIN_FMT, datefmt=DATE_FMT)
    )

    root.addHandler(console_handler)
    root.addHandler(file_handler)


# ═════════════════════════════════════════════════════════════
#  PUBLIC API  —  get a named logger for any module
# ═════════════════════════════════════════════════════════════
def get_logger(name: str) -> logging.Logger:
    """
    Returns a logger named after the calling module.
    Ensures setup_logging() has been called first.

    Example:
        log = get_logger(__name__)
        log.info("Loaded 10 rows from sales_q1.csv")
    """
    setup_logging()
    return logging.getLogger(name)


# ═════════════════════════════════════════════════════════════
#  CONVENIENCE HELPERS  —  structured log messages
# ═════════════════════════════════════════════════════════════
def log_run_start(logger, run_id: str):
    logger.info("=" * 60)
    logger.info(f"PIPELINE RUN STARTED  |  run_id={run_id}")
    logger.info("=" * 60)

def log_run_end(logger, run_id: str, status: str, elapsed: str):
    logger.info("=" * 60)
    logger.info(f"PIPELINE RUN FINISHED |  run_id={run_id}  status={status}  time={elapsed}")
    logger.info("=" * 60)

def log_stage_start(logger, stage: str):
    logger.info(f"--- STAGE START : {stage} ---")

def log_stage_end(logger, stage: str, elapsed: str):
    logger.info(f"--- STAGE END   : {stage}  ({elapsed}) ---")

def log_file_ingested(logger, filename: str, rows: int, cols: int):
    logger.info(f"INGESTED  |  file={filename}  rows={rows}  cols={cols}")

def log_file_skipped_ingest(logger, filename: str, reason: str):
    logger.warning(f"SKIPPED (ingest)  |  file={filename}  reason={reason}")

def log_file_transformed(logger, filename: str, rows_before: int, rows_after: int):
    removed = rows_before - rows_after
    logger.info(
        f"TRANSFORMED  |  file={filename}  "
        f"rows_before={rows_before}  rows_after={rows_after}  duplicates_removed={removed}"
    )

def log_file_loaded(logger, filename: str, table: str, rows: int):
    logger.info(f"LOADED  |  file={filename}  table={table}  rows_inserted={rows}")

def log_file_skipped_load(logger, filename: str, reason: str):
    logger.info(f"SKIPPED (load)  |  file={filename}  reason={reason}")

def log_error(logger, stage: str, filename: str, error: str):
    logger.error(f"ERROR  |  stage={stage}  file={filename}  error={error}")


# ─────────────────────────────────────────────────────────────
# Auto-setup when this module is imported
# ─────────────────────────────────────────────────────────────
setup_logging()
