---
description: Migration Guide from Raspberry Pi to Geekom IT11 (Ubuntu)
---

# 🚀 Migrate Hearth to Geekom (Local AI Powerhouse)

You are moving from a Raspberry Pi (Limited) to an Intel i7 + 32GB RAM (Powerful).
This allows you to run **Llama 3.1 8B** locally with high speed, replacing Gemini and eliminating cloud costs/limits.

## 1. OS Setup (Dual Boot)
1.  **Create Installer**: Download Ubuntu 24.04 LTS ISO and flash to USB using BalenaEtcher.
2.  **BIOS**: Boot Geekom, mash `F7` or `Del` to enter BIOS. Disable "Secure Boot". Set USB as Boot Priority #1.
3.  **Install**:
    *   Select "Install Ubuntu alongside Windows Boot Manager".
    *   Slider: Give Ubuntu **100GB** (This is perfect).
    *   Finish & Reboot.

## 2. Environment Setup (On Ubuntu)
Open Terminal (`Ctrl+Alt+T`) and run:

```bash
# 1. Update System
sudo apt update && sudo apt upgrade -y

# 2. Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker

# 3. Install Ollama (The AI Server)
curl -fsSL https://ollama.com/install.sh | sh
```

## 3. Pull the "Smart" Model
On 32GB RAM, you can comfortably run the **8B** model (much smarter than the Pi's 3B).

```bash
ollama pull llama3.1
# Test it
ollama run llama3.1 "Hello"
```

## 4. Migrate Hearth Data
You can copy your existing setup from the Pi or your Mac.
Assuming you are on the Geekom terminal:

```bash
# Clone your code (or scp from Mac)
git clone https://github.com/YOUR_REPO/hearth.git ~/hearth
cd ~/hearth

# OR Copy from Mac (run this on Mac)
# scp -r ~/Documents/hearth ubuntu@geekom-ip:~/hearth
```

## 5. Configure for Power
Update `docker-compose.yml` on the Geekom to use the better model:

```yaml
environment:
  - AI_PROVIDER=ollama
  - OLLAMA_URL=http://host.docker.internal:11434/api/chat
  - OLLAMA_MODEL=llama3.1  # <--- Change this from llama3.2 to llama3.1 (8B)
```

## 6. Launch
```bash
docker compose up -d --build
```
