
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config.settings import (
    FAISS_INDEX_PATH,
    EMBEDDING_MODEL,
    DENSE_TOP_K,
    FAISS_NPROBE,
    DEVICE,
)
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer


class DenseRetriever:
    def __init__(
        self,
        index_path=FAISS_INDEX_PATH,
        model_name=EMBEDDING_MODEL,
    ):
        self.model = SentenceTransformer(model_name, device=str(DEVICE))
        self.index = faiss.read_index(index_path)
        faiss.ParameterSpace().set_index_parameter(self.index, "nprobe", FAISS_NPROBE)

    def search(self, query, top_k=DENSE_TOP_K):
        query_embedding = self.model.encode(
            [query], normalize_embeddings=True, convert_to_numpy=True
        )
        scores, indices = self.index.search(query_embedding, top_k)

        results = []
        for idx, score in zip(indices[0], scores[0]):
            if idx >= 0:  # FAISS returns -1 for unfilled slots
                results.append((int(idx), float(score)))

        return results
