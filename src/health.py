# src/health.py
import httpx
import sys
import logging
import config

logger = logging.getLogger(__name__)

def check_ollama_ready() -> bool:
    """Verify Ollama is running and the model is available before app starts."""
    try:
        # Check Ollama service is up
        r = httpx.get(f"{config.OLLAMA_BASE_URL}/api/tags", timeout=5)
        r.raise_for_status()

        # Check our specific model is pulled
        models = [m["name"] for m in r.json().get("models", [])]
        model_available = any(config.OLLAMA_MODEL in m for m in models)

        if not model_available:
            logger.error(
                f"Model '{config.OLLAMA_MODEL}' not found in Ollama.\n"
                f"Run: ollama pull {config.OLLAMA_MODEL}"
            )
            return False

        logger.info(f"Ollama ready. Model '{config.OLLAMA_MODEL}' available.")
        return True

    except httpx.ConnectError:
        logger.error(
            "Ollama service not reachable at "
            f"{config.OLLAMA_BASE_URL}. Run: ollama serve"
        )
        return False

def warmup_model():
    """Send a dummy request to load model into GPU memory before first real user query."""
    try:
        import httpx
        httpx.post(
            f"{config.OLLAMA_BASE_URL}/api/generate",
            json={
                "model": config.OLLAMA_MODEL,
                "prompt": "Hello",
                "stream": False,
                "options": {"num_predict": 1}   # generate 1 token only
            },
            timeout=60
        )
        logger.info("Model warm-up complete.")
    except Exception as e:
        logger.warning(f"Warm-up failed (non-critical): {e}")

if __name__ == "__main__":
    if not check_ollama_ready():
        sys.exit(1)