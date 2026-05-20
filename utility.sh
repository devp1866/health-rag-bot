# Linux/macOS
curl -fsSL https://ollama.com/install.sh | sh

# Windows: Download installer from https://ollama.com/download

# Pull the E4B model (correct tag — 9.6GB download)
ollama pull gemma4:e4b

# Verify it downloaded
ollama list

# Quick test to confirm it works
ollama run gemma4:e4b "What are symptoms of diabetes?"




# 1. Make sure Ollama is running in the background
ollama serve   # (if not already running as a service)

# 2. Ingest your health PDFs (run once)
python scripts/ingest.py

# 3. Launch the app
python app.py
# → Open http://localhost:7860









# Remove gemma4:e4b (or whichever you pulled)
ollama rm gemma4:e4b

# Verify it's gone
ollama list

# List all models first
ollama list

# Remove each one (repeat per model shown)
ollama rm gemma4:e4b
ollama rm gemma4:e2b   # if you pulled this too


# Stop the Ollama service first
sudo systemctl stop ollama

# Delete ALL model data, blobs, manifests, cache
sudo rm -rf /usr/share/ollama/.ollama
rm -rf ~/.ollama

# Verify storage is freed
df -h


# Stop and disable the service
sudo systemctl stop ollama
sudo systemctl disable ollama

# Remove the binary
sudo rm /usr/local/bin/ollama

# Remove systemd service file
sudo rm /etc/systemd/system/ollama.service
sudo systemctl daemon-reload

# Remove ollama user and group
sudo userdel ollama
sudo groupdel ollama

# Remove all model data
sudo rm -rf /usr/share/ollama
rm -rf ~/.ollama

echo "Ollama fully removed."

# Check exactly how much space models are taking
du -sh /usr/share/ollama/.ollama/models/
du -sh ~/.ollama/