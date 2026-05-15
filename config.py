from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data" / "documents"
VECTOR_DB_DIR = BASE_DIR / "data" / "vectordb"
BM25_CACHE_PATH = BASE_DIR / "data" / "bm25_cache.pkl"
PARENT_DOCS_PATH = BASE_DIR / "data" / "parent_docs.pkl"

# Create dirs on import
DATA_DIR.mkdir(parents=True, exist_ok=True)
VECTOR_DB_DIR.mkdir(parents=True, exist_ok=True)

# Models
OLLAMA_MODEL = "gemma4:e4b"
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
OLLAMA_BASE_URL = "http://localhost:11434"

# Chunking
CHILD_CHUNK_SIZE = 256
CHILD_CHUNK_OVERLAP = 32
PARENT_CHUNK_SIZE = 1024

# Retrieval
TOP_K_DENSE = 15
TOP_K_SPARSE = 15
TOP_K_FINAL = 5
COLLECTION_NAME = "health_knowledge"

# Generation
TEMPERATURE = 0.1
MAX_TOKENS = 1024