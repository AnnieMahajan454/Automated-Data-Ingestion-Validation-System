"""
scheduler.py  —  Weekly Pipeline Automation
════════════════════════════════════════════
This script keeps running in the background and fires
run_pipeline() automatically on a schedule.

HOW TO USE:
───────────
  Phase 1 — TEST MODE (every minute):
      python scheduler.py --test

  Phase 2 — WEEKLY MODE (every Monday at 08:00):
      python scheduler.py

  Stop the scheduler at any time with:  Ctrl + C
"""

import schedule
import time
import sys
import warnings
import logging
from datetime import datetime

warnings.filterwarnings("ignore")

# ── Import the master pipeline function ──────────────────────
from run_pipeline import run_pipeline

# ─────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────
WEEKLY_DAY  = "monday"     # day of the week to run
WEEKLY_TIME = "08:00"      # time (24hr format)  e.g. "08:00"


# ═════════════════════════════════════════════════════════════
#  LOGGING SETUP
#  Writes scheduler activity to both terminal AND a log file
# ═════════════════════════════════════════════════════════════
logging.basicConfig(
    level   = logging.INFO,
    format  = "%(asctime)s  [SCHEDULER]  %(message)s",
    datefmt = "%Y-%m-%d %H:%M:%S",
    handlers = [
        logging.StreamHandler(sys.stdout),             # print to terminal
        logging.FileHandler("scheduler.log", mode="a") # write to file
    ]
)
log = logging.getLogger(__name__)


# ═════════════════════════════════════════════════════════════
#  SCHEDULED JOB — wraps run_pipeline with logging & safety
# ═════════════════════════════════════════════════════════════
def scheduled_job():
    """
    The function the scheduler calls every time the trigger fires.
    Wraps run_pipeline() with:
      - a start/end log entry
      - try/except so one failure doesn't kill the scheduler
      - result summary logged to scheduler.log
    """
    log.info("=" * 50)
    log.info("⏰  Scheduled trigger fired — starting pipeline")
    log.info("=" * 50)

    try:
        result = run_pipeline()

        # Log the outcome
        log.info(f"✅  Pipeline finished  |  status={result['status']}")
        log.info(f"    Files found   : {result['files_found']}")
        log.info(f"    Files loaded  : {result['files_loaded']}")
        log.info(f"    Files skipped : {result['files_skipped']}")
        log.info(f"    Rows inserted : {result['rows_inserted']}")

        if result["errors"]:
            for err in result["errors"]:
                log.warning(f"⚠️   Error recorded : {err}")

    except Exception as e:
        # Log the error but keep the scheduler alive
        log.error(f"❌  Pipeline crashed unexpectedly: {e}")
        log.error("    Scheduler will continue and retry at next scheduled time.")

    log.info("=" * 50)


# ═════════════════════════════════════════════════════════════
#  COUNTDOWN — shows time until next run
# ═════════════════════════════════════════════════════════════
def show_next_run():
    """Prints when the next scheduled run will fire."""
    next_run = schedule.next_run()
    if next_run:
        print(f"\n  ⏭️  Next run scheduled for: {next_run.strftime('%A %Y-%m-%d at %H:%M:%S')}\n")


# ═════════════════════════════════════════════════════════════
#  MAIN — set up schedule and start the loop
# ═════════════════════════════════════════════════════════════
def main():
    """
    Reads the command-line argument to decide the schedule mode,
    registers the job, then enters the keep-alive loop.
    """

    # ── Detect mode from command-line argument ────────────────
    test_mode = "--test" in sys.argv

    print("\n")
    print("╔" + "═" * 53 + "╗")
    print("║         ⏰  PIPELINE SCHEDULER  —  STARTING        ║")
    print("╚" + "═" * 53 + "╝")

    if test_mode:
        # ── TEST MODE: run every minute ───────────────────────
        schedule.every(1).minutes.do(scheduled_job)

        print(f"\n  🧪  MODE       : TEST (every 1 minute)")
        print(f"  📋  Log file   : scheduler.log")
        print(f"  🛑  To stop    : press Ctrl + C")
        log.info("Scheduler started in TEST MODE — running every 1 minute")

    else:
        # ── WEEKLY MODE: run every Monday at 08:00 ────────────
        schedule.every().monday.at(WEEKLY_TIME).do(scheduled_job)

        print(f"\n  📅  MODE       : WEEKLY  (every {WEEKLY_DAY.capitalize()} at {WEEKLY_TIME})")
        print(f"  📋  Log file   : scheduler.log")
        print(f"  🛑  To stop    : press Ctrl + C")
        log.info(f"Scheduler started in WEEKLY MODE — every {WEEKLY_DAY} at {WEEKLY_TIME}")

    show_next_run()

    # ── Keep-alive loop ───────────────────────────────────────
    # This loop runs forever, waking up every 30 seconds to check
    # whether any scheduled job is due. If yes, it fires it.
    print("  ✅  Scheduler is running. Waiting for next trigger...\n")

    try:
        while True:
            schedule.run_pending()   # fire any jobs whose time has come
            time.sleep(30)           # wait 30 seconds before checking again

    except KeyboardInterrupt:
        # Graceful shutdown on Ctrl+C
        print("\n\n  🛑  Scheduler stopped by user (Ctrl + C)")
        log.info("Scheduler stopped by user.")
        print("  Goodbye!\n")


# ═════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═════════════════════════════════════════════════════════════
if __name__ == "__main__":
    main()
