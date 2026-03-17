
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pyarrow as pa
import pyarrow.parquet as pq
from config.settings import PARQUET_PATH, PROCESSED_DIR, PROCESSED_PARQUET_PATH

CHUNK_SIZE = 50_000


def _build_search_text(tag, summary, fulltext):
    tag = (tag or "").strip()
    summary = (summary or "").strip()

    if tag and summary:
        return tag + " [SEP] " + summary
    elif tag:
        return tag
    elif summary:
        return summary

    fulltext = (fulltext or "").strip()
    return fulltext[:500] if fulltext else ""


def _build_bm25_text(tag, summary, fulltext):
    tag = (tag or "").strip()
    summary = (summary or "").strip()

    if tag and summary:
        return tag + " " + summary
    elif tag:
        return tag
    elif summary:
        return summary

    fulltext = (fulltext or "").strip()
    return fulltext[:500] if fulltext else ""


def preprocess():
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    if os.path.exists(PROCESSED_PARQUET_PATH):
        print(f"Processed dataset already exists at {PROCESSED_PARQUET_PATH}, skipping.")
        return PROCESSED_PARQUET_PATH

    print(f"Reading raw dataset from {PARQUET_PATH} in chunks...")
    parquet_file = pq.ParquetFile(PARQUET_PATH)
    total_rows = parquet_file.metadata.num_rows
    print(f"Total rows: {total_rows:,}")

    #Build output
    input_schema = parquet_file.schema_arrow
    output_schema = input_schema.append(pa.field("search_text", pa.string()))
    output_schema = output_schema.append(pa.field("bm25_text", pa.string()))

    writer = pq.ParquetWriter(PROCESSED_PARQUET_PATH, output_schema)
    processed = 0
    empty_search = 0
    empty_bm25 = 0

    for batch in parquet_file.iter_batches(batch_size=CHUNK_SIZE):
        table = pa.Table.from_batches([batch], schema=input_schema)
        chunk = table.to_pandas()

        #Build the two new columns
        search_texts = []
        bm25_texts = []
        tags = chunk.get("tag")
        summaries = chunk.get("summary")
        fulltexts = chunk.get("fulltext")

        for i in range(len(chunk)):
            tag = tags.iloc[i] if tags is not None else None
            summary = summaries.iloc[i] if summaries is not None else None
            fulltext = fulltexts.iloc[i] if fulltexts is not None else None
            search_texts.append(_build_search_text(tag, summary, fulltext))
            bm25_texts.append(_build_bm25_text(tag, summary, fulltext))

        #Make note of empties for debugging
        empty_search += sum(1 for t in search_texts if t == "")
        empty_bm25 += sum(1 for t in bm25_texts if t == "")

        #Append columns to table and write out
        table = table.append_column("search_text", pa.array(search_texts, type=pa.string()))
        table = table.append_column("bm25_text", pa.array(bm25_texts, type=pa.string()))
        writer.write_table(table)
        processed += len(chunk)
        print(f"  {processed:,} / {total_rows:,} rows processed", end="\r")

    writer.close()
    print(f"\nEmpty search_text: {empty_search:,} / {total_rows:,}")
    print(f"Empty bm25_text: {empty_bm25:,} / {total_rows:,}")

    file_size_gb = os.path.getsize(PROCESSED_PARQUET_PATH) / 1e9
    print(f"Saved to {PROCESSED_PARQUET_PATH} ({file_size_gb:.2f} GB)")

    return PROCESSED_PARQUET_PATH


if __name__ == "__main__":
    preprocess()
