
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config.settings import (
    PROCESSED_PARQUET_PATH,
    EMBEDDINGS_DIR,
    EMBEDDINGS_PATH,
    EMBEDDING_MODEL,
    EMBEDDING_DIM,
    EMBED_BATCH_SIZE_GPU,
    EMBED_BATCH_SIZE_CPU,
    DEVICE,
)
import numpy as np
import pyarrow.parquet as pq
from sentence_transformers import SentenceTransformer

PARQUET_CHUNK_SIZE = 50_000


def embed():
    os.makedirs(EMBEDDINGS_DIR, exist_ok=True)

    if os.path.exists(EMBEDDINGS_PATH):
        print(f"Embeddings already exist at {EMBEDDINGS_PATH}, skipping.")
        return EMBEDDINGS_PATH

    #Get total row count from parquet metadata 
    parquet_file = pq.ParquetFile(PROCESSED_PARQUET_PATH)
    n = parquet_file.metadata.num_rows
    print(f"Total rows to embed: {n:,}")

    print(f"Loading model {EMBEDDING_MODEL} on {DEVICE}...")
    model = SentenceTransformer(EMBEDDING_MODEL, device=str(DEVICE))

    batch_size = EMBED_BATCH_SIZE_GPU if str(DEVICE) != "cpu" else EMBED_BATCH_SIZE_CPU
    print(f"Using batch size {batch_size} on {DEVICE}")

    #Create memory-mapped file for embeddings
    embeddings_mmap = np.memmap(
        EMBEDDINGS_PATH, dtype="float32", mode="w+", shape=(n, EMBEDDING_DIM)
    )

    #Stream through parquet in chunks, encode and write
    row_offset = 0
    for batch in parquet_file.iter_batches(batch_size=PARQUET_CHUNK_SIZE, columns=["search_text"]):
        texts = batch.column("search_text").to_pylist()
        texts = [t if t is not None else "" for t in texts]
        chunk_size = len(texts)

        #Encode each chunk in batches that matches the model batch size
        for start in range(0, chunk_size, batch_size):
            end = min(start + batch_size, chunk_size)
            batch_texts = texts[start:end]
            batch_embeddings = model.encode(
                batch_texts,
                batch_size=batch_size,
                convert_to_numpy=True,
                normalize_embeddings=True,
            )
            embeddings_mmap[row_offset + start : row_offset + end] = batch_embeddings

        row_offset += chunk_size
        print(f"  {row_offset:,} / {n:,} rows embedded", end="\r")

    #Flush
    embeddings_mmap.flush()
    del embeddings_mmap

    #Save shape metadata for later loading
    shape_path = EMBEDDINGS_PATH + ".shape.npy"
    np.save(shape_path, np.array([n, EMBEDDING_DIM]))

    print(f"\nSaved {n:,} embeddings ({EMBEDDING_DIM}d) to {EMBEDDINGS_PATH}")
    print(f"File size: {os.path.getsize(EMBEDDINGS_PATH) / 1e9:.2f} GB")
    return EMBEDDINGS_PATH


if __name__ == "__main__":
    embed()
