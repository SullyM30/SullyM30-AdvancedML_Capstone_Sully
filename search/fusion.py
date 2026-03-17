
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config.settings import RRF_K, RERANK_CANDIDATES


def reciprocal_rank_fusion(*result_lists, k: int = RRF_K, top_n: int = RERANK_CANDIDATES):
    # merge ranked lists from multiple retrievers without normalizing scores
    rrf_scores = {}

    for result_list in result_lists:
        for rank, (doc_idx, _score) in enumerate(result_list):
            if doc_idx not in rrf_scores:
                rrf_scores[doc_idx] = 0.0
            rrf_scores[doc_idx] += 1.0 / (k + rank + 1)

    sorted_results = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
    return sorted_results[:top_n]
