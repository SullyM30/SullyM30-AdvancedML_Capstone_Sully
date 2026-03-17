
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config.settings import RERANKER_MODEL, RESULTS_PER_PAGE, DEVICE
from sentence_transformers import CrossEncoder


class Reranker:
    def __init__(self, model_name=RERANKER_MODEL):
        self.model = CrossEncoder(model_name, device=str(DEVICE))

    def rerank(self, query, candidates, top_k=RESULTS_PER_PAGE):
        if not candidates:
            return []

        pairs = [(query, text) for _, text in candidates]
        scores = self.model.predict(pairs)

        scored = [
            (doc_idx, float(score))
            for (doc_idx, _), score in zip(candidates, scores)
        ]
        scored.sort(key=lambda x: x[1], reverse=True)

        return scored[:top_k]
