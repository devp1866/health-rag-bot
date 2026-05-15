import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pickle
import logging
from src.loader import load_all_documents
from src.chunker import create_parent_child_chunks
from src.vectorstore import build_vectorstore, build_bm25_index
import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

def main():
    logger.info("=== Starting ingestion pipeline ===")

    docs = load_all_documents(config.DATA_DIR)
    if not docs:
        logger.error(f"No documents found in {config.DATA_DIR}. Add PDFs first.")
        return

    parent_docs, child_docs = create_parent_child_chunks(
        docs,
        parent_chunk_size=config.PARENT_CHUNK_SIZE,
        child_chunk_size=config.CHILD_CHUNK_SIZE,
        child_overlap=config.CHILD_CHUNK_OVERLAP
    )

    # Save parent docs for runtime expansion
    with open(config.PARENT_DOCS_PATH, "wb") as f:
        pickle.dump(parent_docs, f)
    logger.info(f"Saved {len(parent_docs)} parent docs")

    # Build indexes
    build_vectorstore(child_docs)
    build_bm25_index(child_docs)

    logger.info("=== Ingestion complete! Run: python app.py ===")

if __name__ == "__main__":
    main()