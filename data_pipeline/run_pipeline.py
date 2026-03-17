
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from data_pipeline.download_dataset import download_dataset
from data_pipeline.preprocess import preprocess
from data_pipeline.build_metadata_db import build_metadata_db
from data_pipeline.embed import embed
from data_pipeline.build_faiss_index import build_faiss_index
from data_pipeline.build_bm25_index import build_bm25_index


def run_pipeline(start_step=0):
    print("running pipeline...")

    if start_step <= 0:
        print("\n[1/6] downloading dataset...")
        t = time.time()
        download_dataset()
        print(f"done in {int(time.time()-t)}s")

    if start_step <= 1:
        print("\n[2/6] preprocessing...")
        t = time.time()
        preprocess()
        print(f"done in {int(time.time()-t)}s")

    if start_step <= 2:
        print("\n[3/6] building metadata db...")
        t = time.time()
        build_metadata_db()
        print(f"done in {int(time.time()-t)}s")

    if start_step <= 3:
        print("\n[4/6] generating embeddings...")
        t = time.time()
        embed()
        print(f"done in {int(time.time()-t)}s")

    if start_step <= 4:
        print("\n[5/6] building FAISS index...")
        t = time.time()
        build_faiss_index()
        print(f"done in {int(time.time()-t)}s")

    if start_step <= 5:
        print("\n[6/6] building BM25 index...")
        t = time.time()
        build_bm25_index()
        print(f"done in {int(time.time()-t)}s")

    print("\ndone.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run the data pipeline")
    parser.add_argument(
        "--start-step",
        type=int,
        default=0,
        help="Step to start from (0-indexed). Use to resume after a failure.",
    )
    args = parser.parse_args()
    run_pipeline(start_step=args.start_step)
