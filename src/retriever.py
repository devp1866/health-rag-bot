import logging
from collections import defaultdict
from langchain.schema import Document
from langchain_community.vectorstores import Chroma
from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder
import config

logger = logging.getLogger(__name__)


class HybridRetriever:
    """
    Production retrieval pipeline:
      1. Dense search  (ChromaDB cosine similarity)
      2. Sparse search (BM25 keyword match)
      3. Reciprocal Rank Fusion (RRF) to merge both lists
      4. Parent-doc expansion  (replace small child chunks with full parent)
      5. Cross-encoder reranking (semantic precision filter)
    """

    def __init__(
        self,
        vectorstore: Chroma,
        bm25: BM25Okapi,
        bm25_docs: list[Document],
        parent_docs: list[Document]
    ):
        self.vectorstore = vectorstore
        self.bm25 = bm25
        self.bm25_docs = bm25_docs
        # Build fast parent_id → Document lookup
        self.parent_store: dict[str, Document] = {
            doc.metadata["doc_id"]: doc
            for doc in parent_docs
            if "doc_id" in doc.metadata
        }
        self.reranker = CrossEncoder(config.RERANKER_MODEL)
        logger.info("HybridRetriever ready")

    # ── 1. Dense retrieval ─────────────────────────────────────────────────
    def _dense_search(self, query: str, k: int) -> list[tuple[Document, float]]:
        return self.vectorstore.similarity_search_with_relevance_scores(query, k=k)

    # ── 2. BM25 retrieval ──────────────────────────────────────────────────
    def _sparse_search(self, query: str, k: int) -> list[tuple[Document, float]]:
        tokens = query.lower().split()
        scores = self.bm25.get_scores(tokens)
        top_idx = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
        max_score = max(scores) if max(scores) > 0 else 1.0
        return [
            (self.bm25_docs[i], scores[i] / max_score)
            for i in top_idx if scores[i] > 0
        ]

    # ── 3. RRF Fusion ──────────────────────────────────────────────────────
    def _rrf(
        self,
        dense: list[tuple[Document, float]],
        sparse: list[tuple[Document, float]],
        k: int = 60
    ) -> list[Document]:
        rrf_scores: dict[str, float] = defaultdict(float)
        doc_map: dict[str, Document] = {}

        for rank, (doc, _) in enumerate(dense):
            key = doc.page_content[:120]
            rrf_scores[key] += 1.0 / (k + rank + 1)
            doc_map[key] = doc

        for rank, (doc, _) in enumerate(sparse):
            key = doc.page_content[:120]
            rrf_scores[key] += 1.0 / (k + rank + 1)
            doc_map[key] = doc

        sorted_keys = sorted(rrf_scores, key=lambda x: rrf_scores[x], reverse=True)
        return [doc_map[k] for k in sorted_keys]

    # ── 4. Parent-doc expansion ────────────────────────────────────────────
    def _expand_to_parents(self, child_docs: list[Document]) -> list[Document]:
        seen, result = set(), []
        for doc in child_docs:
            pid = doc.metadata.get("parent_id")
            if pid and pid not in seen:
                parent = self.parent_store.get(pid, doc)
                result.append(parent)
                seen.add(pid)
            elif not pid:
                result.append(doc)
        return result

    # ── 5. Cross-encoder reranking ─────────────────────────────────────────
    def _rerank(self, query: str, docs: list[Document], top_k: int) -> list[Document]:
        if not docs:
            return []
        pairs = [(query, doc.page_content) for doc in docs]
        scores = self.reranker.predict(pairs)
        ranked = sorted(zip(scores, docs), key=lambda x: x[0], reverse=True)
        return [doc for _, doc in ranked[:top_k]]

    # ── Public interface ───────────────────────────────────────────────────
    def retrieve(self, query: str) -> list[Document]:
        dense_res = self._dense_search(query, config.TOP_K_DENSE)
        sparse_res = self._sparse_search(query, config.TOP_K_SPARSE)
        fused = self._rrf(dense_res, sparse_res)
        enriched = self._expand_to_parents(fused[:12])
        final = self._rerank(query, enriched, config.TOP_K_FINAL)
        logger.info(f"Final docs retrieved: {len(final)}")
        return final