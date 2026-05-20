import time
import json
import logging
from datetime import datetime
from langchain_core.documents import Document
from langchain_ollama import OllamaLLM as Ollama
from langchain_core.prompts import PromptTemplate
from src.retriever import HybridRetriever
import config

logger = logging.getLogger(__name__)

# ── Guardrail keyword list ─────────────────────────────────────────────────
HEALTH_KEYWORDS = {
    "disease", "symptom", "medicine", "treatment", "health", "diet",
    "nutrition", "vaccine", "infection", "hospital", "doctor", "patient",
    "blood", "heart", "lung", "diabetes", "cancer", "fever", "pain",
    "pregnancy", "child", "mental", "exercise", "wellness", "drug",
    "virus", "bacteria", "immune", "therapy", "surgery", "diagnosis",
    "prevention", "care", "illness", "injury", "wound", "bone", "skin",
    "allergy", "chronic", "acute", "obesity", "kidney", "liver", "malaria",
    "tuberculosis", "tb", "hiv", "aids", "covid", "flu", "cholesterol"
}

DISCLAIMER = (
    "\n\n---\n"
    "⚠️ **Medical Disclaimer:** This information is for educational purposes only. "
    "Always consult a qualified healthcare professional for personal medical advice."
)

QUERY_REWRITE_PROMPT = PromptTemplate.from_template(
    "You are a health information assistant.\n"
    "Rewrite the user's question to be precise and suitable for searching medical documentation.\n"
    "Output ONLY the rewritten query — no explanation, no preamble.\n\n"
    "Original: {query}\n"
    "Rewritten:"
)

RAG_PROMPT = PromptTemplate.from_template(
    "You are a trusted, compassionate health education assistant.\n"
    "Answer ONLY using the provided context. If the context lacks enough information, say so clearly.\n"
    "Be clear, precise, and avoid unnecessary medical jargon. Cite which source supports each key claim.\n\n"
    "Context:\n{context}\n\n"
    "Sources available: {sources}\n\n"
    "Question: {question}\n\n"
    "Answer:"
)


class HealthRAGChain:
    def __init__(self, retriever: HybridRetriever):
        self.retriever = retriever
        self.llm = Ollama(
            model=config.OLLAMA_MODEL,
            base_url=config.OLLAMA_BASE_URL,
            temperature=config.TEMPERATURE,
        )

    # ── Fix 1: _call_llm_with_retry is now a proper class method ──────────
    def _call_llm_with_retry(self, prompt: str, retries: int = 3) -> str:
        """Retry LLM calls with exponential backoff — handles Ollama timeouts."""
        for attempt in range(retries):
            try:
                return self.llm.invoke(prompt).strip()
            except Exception as e:
                wait = 2 ** attempt  # 1s, 2s, 4s
                logger.warning(
                    f"LLM call failed (attempt {attempt + 1}): {e}. "
                    f"Retrying in {wait}s..."
                )
                time.sleep(wait)
        raise RuntimeError("LLM failed after 3 retries. Is Ollama running?")

    # ── Fix 2: _log_request is now a proper class method ──────────────────
    def _log_request(self, question: str, result: dict):
        """Log every RAG request for observability and debugging."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "question": question,
            "rewritten_query": result["rewritten_query"],
            "docs_found": result["docs_found"],
            "sources": result["sources"],
            "answer_length": len(result["answer"])
        }
        logger.info(f"RAG_REQUEST: {json.dumps(log_entry)}")

    def _is_health_related(self, query: str) -> bool:
        return any(kw in query.lower() for kw in HEALTH_KEYWORDS)

    def _rewrite_query(self, query: str) -> str:
        try:
            prompt = QUERY_REWRITE_PROMPT.format(query=query)
            # Fix 3: uses _call_llm_with_retry instead of direct llm.invoke
            rewritten = self._call_llm_with_retry(prompt).split("\n")[0]
            logger.info(f"Rewritten: '{query}' → '{rewritten}'")
            return rewritten if rewritten else query
        except Exception:
            return query

    def _format_context(self, docs: list[Document]) -> tuple[str, str]:
        parts, sources = [], set()
        for i, doc in enumerate(docs, 1):
            src = doc.metadata.get("source", "Unknown")
            page = doc.metadata.get("page", "")
            label = f"{src} (p.{page})" if page else src
            sources.add(label)
            parts.append(f"[{i}] {doc.page_content.strip()}")
        return "\n\n".join(parts), ", ".join(sorted(sources))

    def ask(self, question: str) -> dict:
        """Full pipeline: guardrail → rewrite → retrieve → generate → log."""
        if not self._is_health_related(question):
            return {
                "answer": "I can only answer health and medical questions. Please ask something health-related.",
                "sources": [],
                "rewritten_query": question,
                "docs_found": 0
            }

        rewritten = self._rewrite_query(question)
        docs = self.retriever.retrieve(rewritten)

        if not docs:
            return {
                "answer": "I couldn't find relevant health information in my knowledge base for this question.",
                "sources": [],
                "rewritten_query": rewritten,
                "docs_found": 0
            }

        context, sources_str = self._format_context(docs)
        prompt = RAG_PROMPT.format(
            context=context,
            sources=sources_str,
            question=question
        )

        # Fix 3: uses _call_llm_with_retry instead of direct llm.invoke
        answer = self._call_llm_with_retry(prompt) + DISCLAIMER

        result = {
            "answer": answer,
            "sources": list({d.metadata.get("source", "") for d in docs}),
            "rewritten_query": rewritten,
            "docs_found": len(docs)
        }

        # Fix 4: _log_request is now actually called
        self._log_request(question, result)

        return result