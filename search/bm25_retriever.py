
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import bm25s
from config.settings import BM25_INDEX_DIR, BM25_TOP_K


class BM25Retriever:
    def __init__(self, index_dir=BM25_INDEX_DIR):
        self.retriever = bm25s.BM25.load(index_dir, mmap=True)

    def search(self, query, top_k=BM25_TOP_K):
        query_tokens = bm25s.tokenize([query], stopwords="en", stemmer=None)
        results, scores = self.retriever.retrieve(query_tokens, k=top_k)

        doc_indices = results[0].tolist()
        doc_scores = scores[0].tolist()

        return list(zip(doc_indices, doc_scores))
