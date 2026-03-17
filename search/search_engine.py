
import os
import sys
import sqlite3
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from search.bm25_retriever import BM25Retriever
from search.dense_retriever import DenseRetriever
from search.fusion import reciprocal_rank_fusion
from search.reranker import Reranker
from config.settings import (
    RESULTS_PER_PAGE, BM25_TOP_K, DENSE_TOP_K, RERANK_CANDIDATES,
    get_dataset_paths,
)

DEFAULT_DATASET = "opencaselist-2020-2022"


class SearchEngine:
    def __init__(self, dataset_name: str = DEFAULT_DATASET, use_reranker: bool = True):
        paths = get_dataset_paths(dataset_name)
        print(f"Loading dataset: {paths['label']}")
        print("Loading BM25 index...")
        self.bm25 = BM25Retriever(index_dir=paths["bm25"])
        print("Loading FAISS index and embedding model...")
        self.dense = DenseRetriever(index_path=paths["faiss"])
        self.reranker = None
        if use_reranker:
            print("Loading cross-encoder reranker...")
            self.reranker = Reranker()
        self.db_path = paths["db"]
        print("Search engine ready.")

    def _get_card_texts(self, doc_indices):
        conn = sqlite3.connect(self.db_path)
        placeholders = ",".join("?" for _ in doc_indices)

        #Initialize query and fetch text for candidates
        query = f"""
            SELECT rowid, COALESCE(tag, '') || ' ' || COALESCE(summary, '') as search_text
            FROM cards
            WHERE rowid IN ({placeholders})
        """
        cursor = conn.execute(query, doc_indices)
        result = {}

        for rowid, text in cursor:
            result[rowid] = text
        conn.close()
        return result

    def _get_card_metadata(self, doc_indices):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        placeholders = ",".join("?" for _ in doc_indices)

        #Initialize query and fetch text for candidate
        query = f"SELECT rowid, * FROM cards WHERE rowid IN ({placeholders})"
        cursor = conn.execute(query, doc_indices)
        rows = [dict(row) for row in cursor]
        conn.close()

        row_map = {r["rowid"]: r for r in rows}
        return [row_map[idx] for idx in doc_indices if idx in row_map]

    def search(self, query: str, top_k: int = RESULTS_PER_PAGE, use_reranker: bool = True, filters: dict = None):
        t_start = time.time()

        # get a big pool so filtering doesn't starve the results page
        retrieval_k = 1000

        # bm25 + dense retrieval
        bm25_results = self.bm25.search(query, top_k=retrieval_k)
        dense_results = self.dense.search(query, top_k=retrieval_k)

        # combine rankings
        fused = reciprocal_rank_fusion(bm25_results, dense_results)

        # rerank with cross encoder if enabled
        if use_reranker and self.reranker:
            fused_top = fused[:1000]
            doc_indices = [idx for idx, _ in fused_top]

            rowids = [idx + 1 for idx in doc_indices]  # SQLite rowid is 1-indexed, ours is 0-indexed
            texts = self._get_card_texts(rowids)
            candidates = [
                (rowid, texts.get(rowid, ""))
                for rowid in rowids
                if rowid in texts
            ]

            reranked = self.reranker.rerank(query, candidates, top_k=len(candidates))
            final_indices = [idx for idx, _ in reranked]
        else:
            final_indices = [idx + 1 for idx, _ in fused[:top_k]]

        results = self._get_card_metadata(final_indices)

        if filters:
            results = self._apply_filters(results, filters)

        elapsed = time.time() - t_start
        return {"results": results, "timings": {"total": elapsed}}

    def _apply_filters(self, results, filters):
        if filters.get("year_range"):
            lo, hi = filters["year_range"]
            results = [r for r in results if r.get("year") and lo <= int(r["year"]) <= hi]
        if filters.get("event"):
            results = [r for r in results if r.get("event") == filters["event"]]
        if filters.get("level"):
            results = [r for r in results if r.get("level") == filters["level"]]
        if filters.get("side"):
            results = [r for r in results if r.get("side") == filters["side"]]
        return results
