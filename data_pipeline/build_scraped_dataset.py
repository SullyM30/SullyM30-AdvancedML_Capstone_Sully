"""Build a complete search dataset from a scraped caselist CSV.

Takes the output of scraper/run_scraper.py and builds:
  - Processed parquet (with search_text + bm25_text columns)
  - SQLite metadata DB
  - Sentence-transformer embeddings (numpy memmap)
  - FAISS index (factory auto-selected based on dataset size)
  - BM25 index

All artifacts are stored in:
  data/datasets/<dataset_name>/

Usage:
    python -m data_pipeline.build_scraped_dataset ndtceda18 data/scraped/ndtceda18_cards.csv
"""

import os
import sys
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Import config FIRST to set HF_HOME before any HuggingFace import
from config.settings import (
    DATASETS_DIR,
    EMBEDDING_MODEL,
    EMBEDDING_DIM,
    EMBED_BATCH_SIZE_GPU,
    EMBED_BATCH_SIZE_CPU,
    FAISS_NPROBE,
    DEVICE,
)

import sqlite3
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import bm25s
import faiss
from sentence_transformers import SentenceTransformer

CHUNK_SIZE = 50_000

# Columns we want in the SQLite DB (same as main pipeline)
METADATA_COLUMNS = [
    "id", "tag", "cite", "fullcite", "summary", "spoken", "fulltext",
    "markup", "filePath", "opensourcePath", "pocket", "hat", "block",
    "tournament", "round", "side", "year", "event", "level",
    "schoolName", "schoolDisplayName", "teamDisplayName",
]


def _build_search_text(tag, summary, fulltext):
    tag = (tag or "").strip()
    summary = (summary or "").strip()
    if tag or summary:
        parts = [p for p in [tag, summary] if p]
        return " [SEP] ".join(parts)
    return (fulltext or "").strip()[:500]


def _build_bm25_text(tag, summary, fulltext):
    tag = (tag or "").strip()
    summary = (summary or "").strip()
    if tag or summary:
        parts = [p for p in [tag, summary] if p]
        return " ".join(parts)
    return (fulltext or "").strip()[:500]


def _choose_faiss_factory(n: int) -> str:
    """Auto-select FAISS index factory based on dataset size.

    IVF requires at least n_centroids * 39 training vectors.
    """
    if n < 10_000:
        return "Flat"
    elif n < 100_000:
        centroids = max(64, min(256, n // 39))
        return f"IVF{centroids},PQ32x8"
    elif n < 500_000:
        return "IVF1024,PQ48x8"
    else:
        return "IVF4096,PQ48x8"


def build_scraped_dataset(dataset_name: str, csv_path: str):
    """Full pipeline: scraped CSV → parquet → SQLite → embeddings → FAISS → BM25."""

    dataset_dir = os.path.join(DATASETS_DIR, dataset_name)
    os.makedirs(dataset_dir, exist_ok=True)

    parquet_path = os.path.join(dataset_dir, "processed.parquet")
    db_path = os.path.join(dataset_dir, "cards.db")
    embeddings_path = os.path.join(dataset_dir, "embeddings.npy")
    faiss_path = os.path.join(dataset_dir, "faiss.index")
    bm25_dir = os.path.join(dataset_dir, "bm25s_index")

    print(f"Dataset: {dataset_name}")
    print(f"Output directory: {dataset_dir}")
    print(f"Input CSV: {csv_path}")

    # -----------------------------------------------------------------------
    # Step 1: CSV → Parquet (with search_text + bm25_text)
    # -----------------------------------------------------------------------
    if os.path.exists(parquet_path):
        print(f"\n[1/5] Parquet already exists at {parquet_path}, skipping.")
    else:
        print(f"\n[1/5] Converting CSV to parquet with search/BM25 text columns...")

        # First pass: collect all column names
        sample = pd.read_csv(csv_path, dtype=str, keep_default_na=False, nrows=1)
        csv_cols = list(sample.columns)

        # Build output schema (all string)
        all_cols = csv_cols + ["search_text", "bm25_text"]
        schema = pa.schema([(col, pa.string()) for col in all_cols])

        writer = pq.ParquetWriter(parquet_path, schema)
        total_rows = 0

        for chunk in pd.read_csv(csv_path, dtype=str, keep_default_na=False, chunksize=CHUNK_SIZE):
            # Add missing columns as empty strings
            for col in csv_cols:
                if col not in chunk.columns:
                    chunk[col] = ""

            search_texts, bm25_texts = [], []
            for _, row in chunk.iterrows():
                search_texts.append(_build_search_text(
                    row.get("tag"), row.get("summary"), row.get("fulltext")
                ))
                bm25_texts.append(_build_bm25_text(
                    row.get("tag"), row.get("summary"), row.get("fulltext")
                ))

            chunk["search_text"] = search_texts
            chunk["bm25_text"] = bm25_texts

            # Keep only schema columns, fill missing with empty string
            for col in all_cols:
                if col not in chunk.columns:
                    chunk[col] = ""
            chunk = chunk[all_cols]

            table = pa.Table.from_pandas(chunk, schema=schema, preserve_index=False)
            writer.write_table(table)
            total_rows += len(chunk)
            print(f"  {total_rows:,} rows written...", end="\r")

        writer.close()
        size_mb = os.path.getsize(parquet_path) / 1e6
        print(f"\n  Saved {total_rows:,} rows to parquet ({size_mb:.1f} MB)")

    # -----------------------------------------------------------------------
    # Step 2: Parquet → SQLite
    # -----------------------------------------------------------------------
    if os.path.exists(db_path):
        print(f"\n[2/5] SQLite DB already exists at {db_path}, skipping.")
    else:
        print(f"\n[2/5] Building SQLite metadata DB...")
        parquet_file = pq.ParquetFile(parquet_path)
        total_rows = parquet_file.metadata.num_rows
        parquet_cols = parquet_file.schema_arrow.names

        # Only read columns that exist in the parquet
        read_cols = [c for c in METADATA_COLUMNS if c in parquet_cols and c != "id"]

        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")

        processed = 0
        first_batch = True
        global_id = 0

        for batch in parquet_file.iter_batches(batch_size=CHUNK_SIZE, columns=read_cols):
            chunk = batch.to_pandas()
            chunk["id"] = range(global_id, global_id + len(chunk))
            global_id += len(chunk)

            if_exists = "replace" if first_batch else "append"
            chunk.to_sql("cards", conn, if_exists=if_exists, index=False)
            first_batch = False

            processed += len(chunk)
            print(f"  {processed:,} / {total_rows:,} rows written", end="\r")

        print(f"\n  Creating indexes...")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_cards_id ON cards(id)")
        conn.commit()

        count = conn.execute("SELECT COUNT(*) FROM cards").fetchone()[0]
        conn.close()
        db_size_mb = os.path.getsize(db_path) / 1e6
        print(f"  SQLite DB: {count:,} rows, {db_size_mb:.1f} MB")

    # -----------------------------------------------------------------------
    # Step 3: Parquet → Embeddings
    # -----------------------------------------------------------------------
    if os.path.exists(embeddings_path):
        print(f"\n[3/5] Embeddings already exist at {embeddings_path}, skipping.")
    else:
        print(f"\n[3/5] Generating embeddings with {EMBEDDING_MODEL} on {DEVICE}...")
        parquet_file = pq.ParquetFile(parquet_path)
        n = parquet_file.metadata.num_rows
        print(f"  Total rows to embed: {n:,}")

        model = SentenceTransformer(EMBEDDING_MODEL, device=str(DEVICE))
        batch_size = EMBED_BATCH_SIZE_GPU if str(DEVICE) != "cpu" else EMBED_BATCH_SIZE_CPU

        embeddings_mmap = np.memmap(
            embeddings_path, dtype="float32", mode="w+", shape=(n, EMBEDDING_DIM)
        )

        row_offset = 0
        for batch in parquet_file.iter_batches(batch_size=CHUNK_SIZE, columns=["search_text"]):
            texts = batch.column("search_text").to_pylist()
            texts = [t if t is not None else "" for t in texts]
            chunk_size = len(texts)

            for start in range(0, chunk_size, batch_size):
                end = min(start + batch_size, chunk_size)
                batch_emb = model.encode(
                    texts[start:end],
                    batch_size=batch_size,
                    show_progress_bar=False,
                    convert_to_numpy=True,
                    normalize_embeddings=True,
                )
                embeddings_mmap[row_offset + start:row_offset + end] = batch_emb

            row_offset += chunk_size
            print(f"  {row_offset:,} / {n:,} rows embedded", end="\r")

        embeddings_mmap.flush()
        del embeddings_mmap

        np.save(embeddings_path + ".shape.npy", np.array([n, EMBEDDING_DIM]))
        size_gb = os.path.getsize(embeddings_path) / 1e9
        print(f"\n  Saved {n:,} embeddings to {embeddings_path} ({size_gb:.2f} GB)")

    # -----------------------------------------------------------------------
    # Step 4: Embeddings → FAISS index
    # -----------------------------------------------------------------------
    if os.path.exists(faiss_path):
        print(f"\n[4/5] FAISS index already exists at {faiss_path}, skipping.")
    else:
        print(f"\n[4/5] Building FAISS index...")
        shape_path = embeddings_path + ".shape.npy"
        n, dim = (int(x) for x in np.load(shape_path))

        embeddings = np.memmap(embeddings_path, dtype="float32", mode="r", shape=(n, dim))
        factory = _choose_faiss_factory(n)
        print(f"  {n:,} vectors, using factory: {factory}")

        index = faiss.index_factory(dim, factory, faiss.METRIC_INNER_PRODUCT)

        if factory != "Flat":
            train_size = min(max(n // 2, 10_000), n)
            rng = np.random.default_rng(42)
            sample_idx = rng.choice(n, size=train_size, replace=False)
            train_data = np.array(embeddings[sample_idx])
            print(f"  Training on {train_size:,} samples...")
            index.train(train_data)
            del train_data

        ADD_BATCH = 100_000
        print(f"  Adding {n:,} vectors...")
        for start in range(0, n, ADD_BATCH):
            end = min(start + ADD_BATCH, n)
            index.add(np.array(embeddings[start:end]))
            print(f"  {end:,} / {n:,} added", end="\r")

        if factory != "Flat":
            faiss.ParameterSpace().set_index_parameter(index, "nprobe", min(FAISS_NPROBE, 16))

        faiss.write_index(index, faiss_path)
        size_mb = os.path.getsize(faiss_path) / 1e6
        print(f"\n  FAISS index saved ({size_mb:.1f} MB, {index.ntotal:,} vectors)")

    # -----------------------------------------------------------------------
    # Step 5: Parquet → BM25 index
    # -----------------------------------------------------------------------
    if os.path.exists(bm25_dir) and os.listdir(bm25_dir):
        print(f"\n[5/5] BM25 index already exists at {bm25_dir}, skipping.")
    else:
        print(f"\n[5/5] Building BM25 index...")
        parquet_file = pq.ParquetFile(parquet_path)
        n = parquet_file.metadata.num_rows
        print(f"  Loading {n:,} bm25_text values...")

        # Collect all texts (BM25 needs full corpus in memory)
        texts = []
        for batch in parquet_file.iter_batches(batch_size=CHUNK_SIZE, columns=["bm25_text"]):
            texts.extend(batch.column("bm25_text").to_pylist())
        texts = [t if t is not None else "" for t in texts]

        print("  Tokenizing corpus...")
        corpus_tokens = bm25s.tokenize(texts, stopwords="en", stemmer=None)
        del texts

        print("  Building BM25 index...")
        retriever = bm25s.BM25()
        retriever.index(corpus_tokens)

        os.makedirs(bm25_dir, exist_ok=True)
        retriever.save(bm25_dir)
        print(f"  BM25 index saved to {bm25_dir}")

    print(f"\n{'='*60}")
    print(f"Dataset '{dataset_name}' is ready.")
    print(f"  DB:          {db_path}")
    print(f"  FAISS index: {faiss_path}")
    print(f"  BM25 index:  {bm25_dir}")
    print(f"  Embeddings:  {embeddings_path}")
    print(f"{'='*60}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Build search indexes from a scraped caselist CSV"
    )
    parser.add_argument("dataset_name", help="Dataset name (e.g., ndtceda18)")
    parser.add_argument("csv_path", help="Path to the scraped cards CSV")
    args = parser.parse_args()

    build_scraped_dataset(args.dataset_name, args.csv_path)
