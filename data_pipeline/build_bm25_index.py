
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import bm25s
from tqdm import tqdm
from config.settings import PROCESSED_PARQUET_PATH, BM25_INDEX_DIR, INDEX_DIR


def build_bm25_index():
    os.makedirs(INDEX_DIR, exist_ok=True)

    if os.path.exists(BM25_INDEX_DIR) and os.listdir(BM25_INDEX_DIR):
        print(f"BM25 index already exists at {BM25_INDEX_DIR}, skipping.")
        return BM25_INDEX_DIR

    print(f"Loading processed dataset from {PROCESSED_PARQUET_PATH}...")
    df = pd.read_parquet(PROCESSED_PARQUET_PATH, columns=["bm25_text"])
    texts = df["bm25_text"].fillna("").tolist()
    print(f"Loaded {len(texts):,} texts.")

    print("Tokenizing corpus...")
    corpus_tokens = bm25s.tokenize(texts, stopwords="en", stemmer=None)

    print("Building BM25 index...")
    retriever = bm25s.BM25()
    retriever.index(corpus_tokens)

    print(f"Saving BM25 index to {BM25_INDEX_DIR}...")
    os.makedirs(BM25_INDEX_DIR, exist_ok=True)
    retriever.save(BM25_INDEX_DIR)

    print("Done.")
    return BM25_INDEX_DIR


if __name__ == "__main__":
    build_bm25_index()
