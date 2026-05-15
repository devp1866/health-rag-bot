import pickle
import logging
from pathlib import Path
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document
from rank_bm25 import BM25Okapi
import config

logger = logging.getLogger(__name__)

def get_embedding_model() -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(
        model_name=config.EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True}
    )

def build_vectorstore(child_docs: list[Document]) -> Chroma:
    embeddings = get_embedding_model()
    vectorstore = Chroma.from_documents(
        documents=child_docs,
        embedding=embeddings,
        collection_name=config.COLLECTION_NAME,
        persist_directory=str(config.VECTOR_DB_DIR),
        collection_metadata={"hnsw:space": "cosine"}
    )
    logger.info(f"ChromaDB built with {len(child_docs)} child chunks")
    return vectorstore

def load_vectorstore() -> Chroma:
    embeddings = get_embedding_model()
    return Chroma(
        collection_name=config.COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(config.VECTOR_DB_DIR)
    )

def build_bm25_index(docs: list[Document]) -> BM25Okapi:
    tokenized = [doc.page_content.lower().split() for doc in docs]
    bm25 = BM25Okapi(tokenized)
    with open(config.BM25_CACHE_PATH, "wb") as f:
        pickle.dump({"bm25": bm25, "docs": docs}, f)
    logger.info(f"BM25 index built with {len(docs)} docs")
    return bm25

def load_bm25_index() -> tuple[BM25Okapi, list[Document]]:
    with open(config.BM25_CACHE_PATH, "rb") as f:
        data = pickle.load(f)
    return data["bm25"], data["docs"]