
import os
import sys
import sqlite3

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pyarrow.parquet as pq
from config.settings import PROCESSED_PARQUET_PATH, METADATA_DB, METADATA_COLUMNS

CHUNK_SIZE = 50_000


def build_metadata_db():
    if os.path.exists(METADATA_DB):
        print(f"Metadata DB already exists at {METADATA_DB}, skipping.")
        return METADATA_DB

    os.makedirs(os.path.dirname(METADATA_DB), exist_ok=True)

    print(f"Reading processed dataset from {PROCESSED_PARQUET_PATH} in chunks...")
    parquet_file = pq.ParquetFile(PROCESSED_PARQUET_PATH)
    total_rows = parquet_file.metadata.num_rows

    parquet_columns = parquet_file.schema_arrow.names
    available_cols = [c for c in METADATA_COLUMNS if c in parquet_columns]
    missing_cols = [c for c in METADATA_COLUMNS if c not in parquet_columns]
    if missing_cols:
        print(f"Warning: Missing columns in dataset: {missing_cols}")

    needs_id = "id" not in parquet_columns
    read_cols = [c for c in available_cols if c in parquet_columns]

    print(f"Writing to SQLite at {METADATA_DB}...")
    conn = sqlite3.connect(METADATA_DB)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")

    processed = 0
    global_id = 0

    conn.execute("DROP TABLE IF EXISTS cards")

    for batch in parquet_file.iter_batches(batch_size=CHUNK_SIZE, columns=read_cols):
        chunk = batch.to_pandas()

        if needs_id:
            chunk["id"] = range(global_id, global_id + len(chunk))
            global_id += len(chunk)

        chunk.to_sql("cards", conn, if_exists="append", index=False)

        processed += len(chunk)
        print(f"  {processed:,} / {total_rows:,} rows written", end="\r")

    print(f"\n{processed:,} rows written. Creating indexes...")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_cards_id ON cards(id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_cards_year ON cards(year)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_cards_event ON cards(event)")
    conn.commit()

    count = conn.execute("SELECT COUNT(*) FROM cards").fetchone()[0]
    conn.close()

    db_size_gb = os.path.getsize(METADATA_DB) / 1e9
    print(f"SQLite database: {count:,} rows, {db_size_gb:.2f} GB")

    return METADATA_DB


if __name__ == "__main__":
    build_metadata_db()
