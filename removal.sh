sudo systemctl stop ollama
sudo systemctl disable ollama
sudo systemctl daemon-reload


# Remove the main binary
sudo rm -f /usr/local/bin/ollama

# Remove the library folder (your install location)
sudo rm -rf /usr/local/lib/ollama

# Remove systemd service file
sudo rm -f /etc/systemd/system/ollama.service
sudo rm -f /etc/systemd/system/default.target.wants/ollama.service

sudo systemctl daemon-reload



# Primary model storage (blobs, manifests, all downloaded models)
sudo rm -rf /usr/share/ollama

# User-level ollama config and cache
rm -rf ~/.ollama

# Any leftover in local share
rm -rf ~/.local/share/ollama

# Check nothing remains
find / -name "*ollama*" 2>/dev/null





sudo userdel -r ollama 2>/dev/null
sudo groupdel ollama 2>/dev/null
sudo groupdel render 2>/dev/null   # only if it was created by ollama installer



which ollama              # should return nothing
ollama --version          # should say: command not found
systemctl status ollama   # should say: could not be found
find / -name "*ollama*" 2>/dev/null   # should return nothing




sudo apt clean          # removes all cached .deb packages
sudo apt autoclean      # removes outdated cached packages
sudo apt autoremove -y  # removes unused dependency packages





pip cache purge
pip3 cache purge



rm -rf ~/.cache/thumbnails/*
rm -rf ~/.cache/pip/*
rm -rf ~/.cache/huggingface/*    # HuggingFace model cache (sentence-transformers etc.)
rm -rf ~/.cache/torch/*          # PyTorch model cache





# Check how much journal logs are taking
journalctl --disk-usage

# Keep only last 3 days
sudo journalctl --vacuum-time=3d

# OR cap to 100MB
sudo journalctl --vacuum-size=100M




sudo rm -rf /tmp/*
sudo rm -rf /var/tmp/*




# Overall disk usage
df -h

# Find top 10 biggest directories on your system
sudo du -h / --max-depth=4 2>/dev/null | sort -rh | head -20

# Your home folder specifically
du -sh ~/*  | sort -rh | head -15