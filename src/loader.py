import fitz  # pymupdf
from pathlib import Path
from langchain_core.documents import Document
import logging

logger = logging.getLogger(__name__)

def load_pdf(filepath: Path) -> list[Document]:
    docs = []
    try:
        pdf = fitz.open(str(filepath))
        for page_num, page in enumerate(pdf):
            text = page.get_text("text").strip()
            if len(text) < 80:           # skip nearly-empty pages
                continue
            # Clean up text
            text = " ".join(text.split())
            docs.append(Document(
                page_content=text,
                metadata={
                    "source": filepath.name,
                    "page": page_num + 1,
                    "total_pages": len(pdf),
                    "file_type": "pdf"
                }
            ))
        pdf.close()
        logger.info(f"Loaded {len(docs)} pages from {filepath.name}")
    except Exception as e:
        logger.error(f"Error loading {filepath}: {e}")
    return docs

def load_txt(filepath: Path) -> list[Document]:
    try:
        text = filepath.read_text(encoding="utf-8").strip()
        return [Document(
            page_content=text,
            metadata={"source": filepath.name, "page": 1, "file_type": "txt"}
        )]
    except Exception as e:
        logger.error(f"Error loading {filepath}: {e}")
        return []

def load_all_documents(data_dir: Path) -> list[Document]:
    all_docs = []
    loaders = {".pdf": load_pdf, ".txt": load_txt}
    for filepath in sorted(data_dir.iterdir()):
        suffix = filepath.suffix.lower()
        if suffix in loaders:
            all_docs.extend(loaders[suffix](filepath))
    logger.info(f"Total raw pages loaded: {len(all_docs)}")
    return all_docs