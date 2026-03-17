
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config.settings import (
    HF_DATASET_NAME, HF_DATA_FILES, RAW_DIR, PARQUET_PATH, HF_CACHE_DIR,
)
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from huggingface_hub import hf_hub_download

CHUNK_SIZE = 50_000  # rows per chunk


def download_dataset():
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(HF_CACHE_DIR, exist_ok=True)

    if os.path.exists(PARQUET_PATH):
        print(f"Dataset already exists at {PARQUET_PATH}, skipping download.")
        return PARQUET_PATH

    print(f"Downloading {HF_DATASET_NAME} from HuggingFace...")
    print(f"Files: {HF_DATA_FILES}")
    print(f"Cache directory: {HF_CACHE_DIR}")

    #Download and stream
    all_string_schema = None
    writer = None
    total_rows = 0

    #First, collect column names from all files to build a unified schema
    all_columns = []
    csv_paths = []
    for f in HF_DATA_FILES:
        print(f"  Downloading/locating {f}...")
        csv_path = hf_hub_download(
            repo_id=HF_DATASET_NAME,
            filename=f,
            repo_type="dataset",
            cache_dir=os.path.join(HF_CACHE_DIR, "hub"),
        )
        csv_paths.append(csv_path)
        header = pd.read_csv(csv_path, dtype=str, nrows=0)
        for col in header.columns:
            if col not in all_columns:
                all_columns.append(col)

    all_string_schema = pa.schema([(col, pa.string()) for col in all_columns])
    writer = pq.ParquetWriter(PARQUET_PATH, all_string_schema)

    #Second, stream each file in chunks
    for f, csv_path in zip(HF_DATA_FILES, csv_paths):
        print(f"  Streaming {f} in chunks of {CHUNK_SIZE:,}...")
        file_rows = 0
        for chunk in pd.read_csv(csv_path, dtype=str, chunksize=CHUNK_SIZE):
            # Add any missing columns as None
            for col in all_columns:
                if col not in chunk.columns:
                    chunk[col] = None
            chunk = chunk[all_columns]

            table = pa.Table.from_pandas(chunk, schema=all_string_schema, preserve_index=False)
            writer.write_table(table)

            file_rows += len(chunk)
            total_rows += len(chunk)
            print(f"    {file_rows:,} rows processed", end="\r")

        print(f"    {file_rows:,} rows total")

    if writer is not None:
        writer.close()

    file_size_gb = os.path.getsize(PARQUET_PATH) / 1e9
    print(f"Saved {total_rows:,} rows to {PARQUET_PATH} ({file_size_gb:.2f} GB)")

    return PARQUET_PATH


if __name__ == "__main__":
    download_dataset()
