# CardIt — Debate Evidence Search Engine

A hybrid semantic and keyword search engine over competitive debate evidence cards, built on top of the OpenCaselist disclosure database.

---

## Overview

Debate evidence ("cards") are short, quoted paragraphs from academic sources used to support arguments in policy and LD debate. This tool indexes hundreds of thousands of cards and lets you search them by meaning — not just keywords — using a combination of BM25 sparse retrieval and dense vector search (FAISS + sentence-transformers).

---

## Setup

```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

---

## Building the Dataset

There are two ways to get cards into the search engine.

---

### Option A — HuggingFace Baseline (2020–2022)

Uses a pre-scraped open-source dataset of ~2.5 million cards hosted on HuggingFace (`Yusuf5/OpenCaselist`). No API credentials needed.

**Step 1 — Download the raw CSVs and convert to parquet**
```bash
python -m data_pipeline.download_dataset
```
For example, this downloads `evidence-2020.csv`, `evidence-2021.csv`, `evidence-2022.csv` (~27 GB) and merges them into a single parquet file. Streams in 50k-row chunks to stay within RAM limits.

**Step 2 — Run the full pipeline**
```bash
python -m data_pipeline.run_pipeline
```
Builds in sequence:
1. Preprocessed parquet (adds `search_text` and `bm25_text` columns)
2. SQLite metadata database (`data/cards.db`)
3. Sentence-transformer embeddings (`data/embeddings/embeddings.npy`)
4. FAISS index (`data/indexes/faiss_ivfpq.index`)
5. BM25 index (`data/indexes/bm25s_index/`)

Each step is skipped automatically if its output already exists.

---

### Option B — Scraper Pipeline (Fresh Evidence)

Scrapes directly from [OpenCaselist](https://opencaselist.com) via its REST API. Requires a `caselist_token` cookie from a logged-in Tabroom session.

**Step 1 — Bulk download and parse**
```bash
python -m scraper.run_bulk <caselist> --cookie <your_token>
```

Examples:
```bash
# Download all disclosed rounds for hspf25
python -m scraper.run_bulk hspf25 --cookie abc123

# Filter to only TOC rounds
python -m scraper.run_bulk hspf25 --cookie abc123 --tournaments TOC

# Custom output path
python -m scraper.run_bulk hspf25 --cookie abc123 --output data/scraped/toc25.csv
```

This downloads the latest weekly ZIP archive from OpenCaselist, extracts all `.docx` files, parses each one into structured cards (tag, cite, full text, underlines, side, tournament), and exports them to a CSV.

**Step 2 — Build the search index**
```bash
python -m data_pipeline.build_scraped_dataset <name> <csv_path>
```

Example:
```bash
python -m data_pipeline.build_scraped_dataset toc25 data/scraped/hspf25_TOC.csv
```

Output is saved to `data/datasets/toc25/` and includes the same five artifacts as the HuggingFace pipeline (parquet, SQLite, embeddings, FAISS, BM25).

---

## Getting Your Cookie

1. Log in to [opencaselist.com](https://opencaselist.com)
2. Open DevTools → Application → Cookies
3. Copy the value of `caselist_token`

---

## Running the Search UI

```bash
streamlit run ui/app.py
```

Opens at `http://localhost:8501`. The sidebar lets you select which dataset to search and apply filters (year, event, side). Queries use hybrid retrieval — BM25 for keyword precision, FAISS for semantic similarity — fused with Reciprocal Rank Fusion and re-ranked by a cross-encoder.

---

## Project Structure

```
config/             Settings and dataset path registry
scraper/            OpenCaselist API client and bulk downloader
data_pipeline/      CSV → parquet → SQLite → embeddings → FAISS → BM25
search/             BM25 retriever, dense retriever, RRF fusion, re-ranker
ui/                 Streamlit frontend
```
