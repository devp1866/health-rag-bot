import pickle
import logging
import gradio as gr
from src.chain import HealthRAGChain
from src.retriever import HybridRetriever
from src.vectorstore import load_vectorstore, load_bm25_index
import config
from src.health import warmup_model  # Ensure warmup_model is defined in health.py


# app.py — first thing before loading chain
from src.health import check_ollama_ready
import sys

if not check_ollama_ready():
    print("ERROR: Ollama not ready. See logs above.")
    sys.exit(1)

# ... rest of app loads only if Ollama is confirmed ready
warmup_model()  # Optional: warm up model before loading chain

logging.basicConfig(level=logging.INFO)

def load_chain() -> HealthRAGChain:
    vectorstore = load_vectorstore()
    bm25, bm25_docs = load_bm25_index()
    with open(config.PARENT_DOCS_PATH, "rb") as f:
        parent_docs = pickle.load(f)
    retriever = HybridRetriever(vectorstore, bm25, bm25_docs, parent_docs)
    return HealthRAGChain(retriever)

chain = load_chain()

def chat(message: str, history: list) -> str:
    result = chain.ask(message)
    response = result["answer"]
    if result["sources"]:
        response += f"\n\n📚 **Sources:** {', '.join(result['sources'])}"
    if result["rewritten_query"] != message:
        response += f"\n\n🔍 *Interpreted as: {result['rewritten_query']}*"
    return response

with gr.Blocks(title="HealthBot", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🏥 HealthBot — Offline Health Literacy Assistant")
    gr.Markdown(
        "**Powered by Gemma 4 via Ollama** · Runs 100% offline · "
        "Uses WHO, CDC & MoHFW guidelines · No data leaves your device."
    )
    gr.ChatInterface(
        fn=chat,
        examples=[
            "What are early warning signs of diabetes?",
            "How is tuberculosis spread and prevented?",
            "What nutrition does a pregnant woman need?",
            "How do vaccines protect against diseases?",
            "What should I do if I have high fever?",
        ]
    )

if __name__ == "__main__":
    demo.launch(server_port=7860, share=False)