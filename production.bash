# Get the exact digest after pulling
ollama show gemma4:e4b --modelinfo | grep digest

# config.py — pin exact tag, document the digest in comments
OLLAMA_MODEL = "gemma4:e4b"
# Digest: c6eb396dbd59 — pinned April 2026, update intentionally only



# Add to your ~/.bashrc or ~/.profile permanently
echo 'export OLLAMA_KEEP_ALIVE=-1' >> ~/.bashrc
source ~/.bashrc

# Restart Ollama service to apply
sudo systemctl restart ollama