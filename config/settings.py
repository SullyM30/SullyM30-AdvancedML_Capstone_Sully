import os
import torch

# paths
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
EMBEDDINGS_DIR = os.path.join(DATA_DIR, "embeddings")
INDEX_DIR = os.path.join(DATA_DIR, "indexes")

# HuggingFace Cache
HF_CACHE_DIR = os.path.join(DATA_DIR, "hf_cache")
os.environ["HF_HOME"] = HF_CACHE_DIR
os.environ["HF_DATASETS_CACHE"] = os.path.join(HF_CACHE_DIR, "datasets")
os.environ["TRANSFORMERS_CACHE"] = os.path.join(HF_CACHE_DIR, "transformers")

METADATA_DB = os.path.join(DATA_DIR, "cards.db")
FAISS_INDEX_PATH = os.path.join(INDEX_DIR, "faiss_ivfpq.index")
BM25_INDEX_DIR = os.path.join(INDEX_DIR, "bm25s_index")
EMBEDDINGS_PATH = os.path.join(EMBEDDINGS_DIR, "embeddings.npy")

DATASETS_DIR = os.path.join(DATA_DIR, "datasets")

BUILTIN_DATASETS = {
    "opencaselist-2020-2022": {
        "label": "OpenCaselist 2020-2022",
        "db": METADATA_DB,
        "faiss": FAISS_INDEX_PATH,
        "bm25": BM25_INDEX_DIR,
        "embeddings": EMBEDDINGS_PATH,
    }
}


def get_dataset_paths(name):
    if name in BUILTIN_DATASETS:
        return BUILTIN_DATASETS[name]
    dataset_dir = os.path.join(DATASETS_DIR, name)
    return {
        "label": name,
        "db": os.path.join(dataset_dir, "cards.db"),
        "faiss": os.path.join(dataset_dir, "faiss.index"),
        "bm25": os.path.join(dataset_dir, "bm25s_index"),
        "embeddings": os.path.join(dataset_dir, "embeddings.npy"),
        "dir": dataset_dir,
    }


#dataset
HF_DATASET_NAME = "Yusuf5/OpenCaselist"
HF_DATA_FILES = ["evidence-2020.csv", "evidence-2021.csv", "evidence-2022.csv"]
PARQUET_PATH = os.path.join(RAW_DIR, "opencaselist.parquet")
PROCESSED_PARQUET_PATH = os.path.join(PROCESSED_DIR, "opencaselist_processed.parquet")

#models
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
EMBEDDING_DIM = 384
MAX_SEQ_LENGTH = 256

#faiss index config
FAISS_INDEX_FACTORY = "IVF4096,PQ48x8"
FAISS_TRAIN_SAMPLE = 500000
FAISS_NPROBE = 32

#search params
BM25_TOP_K = 150
DENSE_TOP_K = 150
RRF_K = 60
RERANK_CANDIDATES = 200
RESULTS_PER_PAGE = 20

#embedding batch sizes
EMBED_BATCH_SIZE_GPU = 512
EMBED_BATCH_SIZE_CPU = 64

def get_device():
    if torch.cuda.is_available():
        return torch.device("cuda")
    elif hasattr(torch, "xpu") and torch.xpu.is_available():
        return torch.device("xpu")
    else:
        return torch.device("cpu")

DEVICE = get_device()

#sqlite metadata columns
METADATA_COLUMNS = [
    "id", "tag", "cite", "fullcite", "summary", "spoken", "fulltext",
    "markup", "filePath", "opensourcePath", "pocket", "hat", "block",
    "tournament", "round", "side", "year", "event", "level",
    "schoolName", "schoolDisplayName", "teamDisplayName", "duplicateCount",
]
