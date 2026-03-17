# CardIt — Debate Card Search Engine

A hybrid ML search engine for debate evidence cards. Searches from the OpenCaselist dataset using a 3-stage pipeline: BM25 sparse retrieval + dense semantic retrieval (FAISS) + cross-encoder re-ranking.
---

## Setup

**Python 3.10+ required.**

```bash
pip install -r requirements.txt
```

If you have a GPU:
```bash
pip install faiss-gpu
```

---

## Building the Dataset

This downloads ~5M debate cards from HuggingFace, preprocesses them, builds a SQLite metadata database, generates embeddings, and builds both a FAISS and BM25 index. May take a few hours for entire pipeline to generate embeddings, based on the device's hardware. 

```bash
python -m data_pipeline.run_pipeline
```
---

## Running a Search

You an create a quick python script to do a test search like below:

```python
from search.search_engine import SearchEngine

engine = SearchEngine(use_reranker=True)

results = engine.search("climate change causes extinction")
for card in results["results"]:
    print(card["tag"])
    print(card["cite"])
    print()
```

To skip the cross-encoder:
```python
results = engine.search("your query here", use_reranker=False)
```

To filter by year or event:
```python
results = engine.search(
    "nuclear war",
    filters={"year_range": (2021, 2022), "event": "cx"}
)
```

---

## Project Structure

```
config/          - settings and paths
data_pipeline/   - download, preprocess, build indexes
search/          - BM25, dense retrieval, reranking
```

---
