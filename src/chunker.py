import uuid
import logging
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

def create_parent_child_chunks(
    documents: list[Document],
    parent_chunk_size: int = 1024,
    child_chunk_size: int = 256,
    child_overlap: int = 32
) -> tuple[list[Document], list[Document]]:
    """
    Parent-Child chunking strategy:
      - Parent chunks  →  stored for context retrieval (large, readable)
      - Child chunks   →  indexed in vector store (small, precise for search)
    Each child carries a parent_id so we can look up its full parent at query time.
    """
    parent_splitter = RecursiveCharacterTextSplitter(
        chunk_size=parent_chunk_size,
        chunk_overlap=128,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    child_splitter = RecursiveCharacterTextSplitter(
        chunk_size=child_chunk_size,
        chunk_overlap=child_overlap,
        separators=["\n\n", "\n", ". ", " ", ""]
    )

    parent_docs, child_docs = [], []

    for doc in documents:
        parents = parent_splitter.split_documents([doc])
        for parent in parents:
            parent_id = str(uuid.uuid4())
            parent.metadata["doc_id"] = parent_id
            parent.metadata["chunk_type"] = "parent"
            parent_docs.append(parent)

            children = child_splitter.split_documents([parent])
            for idx, child in enumerate(children):
                child.metadata["parent_id"] = parent_id
                child.metadata["chunk_type"] = "child"
                child.metadata["child_index"] = idx
                child_docs.append(child)

    logger.info(f"Created {len(parent_docs)} parent chunks, {len(child_docs)} child chunks")
    return parent_docs, child_docs