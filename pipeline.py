import os
import pandas as pd
from logger import get_logger, log_file_ingested, log_file_skipped_ingest, log_error

log = get_logger("pipeline")

RAW_FOLDER = "data/raw"

def get_csv_files(folder):
    csv_files = []
    for filename in os.listdir(folder):
        if filename.endswith(".csv"):
            csv_files.append(os.path.join(folder, filename))
    log.info(f"Scanned folder '{folder}' — found {len(csv_files)} CSV file(s)")
    return csv_files

def load_csv(filepath):
    filename = os.path.basename(filepath)
    try:
        df = pd.read_csv(filepath, on_bad_lines="warn")
        if df.empty:
            log.warning(f"SKIPPED '{filename}' — file is empty")
            log_file_skipped_ingest(log, filename, "empty file")
            return None

        log_file_ingested(log, filename, df.shape[0], df.shape[1])

        missing = df.isnull().sum()
        missing = missing[missing > 0]
        if not missing.empty:
            log.debug(f"  Missing values in '{filename}': {missing.to_dict()}")

        return df

    except pd.errors.EmptyDataError:
        log_error(log, "ingest", filename, "EmptyDataError")
        log_file_skipped_ingest(log, filename, "EmptyDataError")
        return None
    except pd.errors.ParserError as e:
        log_error(log, "ingest", filename, f"ParserError: {e}")
        log_file_skipped_ingest(log, filename, "ParserError — check column count")
        return None
    except Exception as e:
        log_error(log, "ingest", filename, str(e))
        return None

def load_all_csvs(folder):
    csv_files  = get_csv_files(folder)
    loaded     = {}
    skipped    = []

    for filepath in csv_files:
        filename = os.path.basename(filepath)
        df = load_csv(filepath)
        if df is not None:
            loaded[filename] = df
        else:
            skipped.append(filename)

    log.info(
        f"Ingestion complete — loaded={len(loaded)}  skipped={len(skipped)}"
    )
    if skipped:
        log.warning(f"Skipped files: {skipped}")

    return loaded

if __name__ == "__main__":
    data = load_all_csvs(RAW_FOLDER)
    for name, df in data.items():
        print(f"  {name}: {df.shape[0]} rows x {df.shape[1]} cols")
