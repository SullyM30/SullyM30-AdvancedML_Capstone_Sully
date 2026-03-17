
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import faiss
from config.settings import (
    EMBEDDINGS_PATH,
    FAISS_INDEX_PATH,
    INDEX_DIR,
    EMBEDDING_DIM,
    FAISS_INDEX_FACTORY,
    FAISS_TRAIN_SAMPLE,
    FAISS_NPROBE,
)


def build_faiss_index():
    os.makedirs(INDEX_DIR, exist_ok=True)

    if os.path.exists(FAISS_INDEX_PATH):
        print(f"FAISS index already exists at {FAISS_INDEX_PATH}, skipping.")
        return FAISS_INDEX_PATH

    #Load embeddings
    shape_path = EMBEDDINGS_PATH + ".shape.npy"
    n, dim = np.load(shape_path).astype(int)
    print(f"Loading {n:,} embeddings of dim {dim}...")

    embeddings = np.memmap(EMBEDDINGS_PATH, dtype="float32", mode="r", shape=(n, dim))

    #Create the index
    print(f"Creating FAISS index: {FAISS_INDEX_FACTORY}")
    index = faiss.index_factory(EMBEDDING_DIM, FAISS_INDEX_FACTORY, faiss.METRIC_INNER_PRODUCT)

    # Train on a random sample
    print(f"Sampling {FAISS_TRAIN_SAMPLE:,} vectors for training...")
    np.random.seed(42)
    sample_idx = np.random.choice(n, size=min(FAISS_TRAIN_SAMPLE, n), replace=False)
    train_data = np.array(embeddings[sample_idx])

    print("Training index...")
    index.train(train_data)

    #Add all vectors in batches
    batch_size = 100_000
    print(f"Adding {n:,} vectors in batches of {batch_size:,}...")
    for start in range(0, n, batch_size):
        end = min(start + batch_size, n)
        batch = np.array(embeddings[start:end])
        index.add(batch)
        if (start // batch_size) % 10 == 0:
            print(f"  Added {end:,} / {n:,}")

    #Set search parameters
    faiss.ParameterSpace().set_index_parameter(index, "nprobe", FAISS_NPROBE)

    #Save
    print(f"Saving index to {FAISS_INDEX_PATH}...")
    faiss.write_index(index, FAISS_INDEX_PATH)

    file_size = os.path.getsize(FAISS_INDEX_PATH) / 1e6
    print(f"Index saved. Size: {file_size:.1f} MB, Vectors: {index.ntotal:,}")
    return FAISS_INDEX_PATH


if __name__ == "__main__":
    build_faiss_index()
