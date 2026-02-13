#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Hearth Environment Setup...${NC}"

# 1. Update and Install System Dependencies
echo -e "${GREEN}[1/4] Updating system and installing dependencies...${NC}"
sudo apt-get update
sudo apt-get install -y ffmpeg curl git

# 2. Install Docker (Reference: https://get.docker.com)
if ! command -v docker &> /dev/null; then
    echo -e "${GREEN}[2/4] Installing Docker...${NC}"
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    # Add current user to docker group
    sudo usermod -aG docker $USER
    echo "Docker installed. You may need to logout and login again for group changes to take effect."
    rm get-docker.sh
else
    echo -e "${GREEN}[2/4] Docker already installed.${NC}"
fi

# 3. Install Ollama (Native/Host)
if ! command -v ollama &> /dev/null; then
    echo -e "${GREEN}[3/4] Installing Ollama (Host)...${NC}"
    curl -fsSL https://ollama.com/install.sh | sh
else
    echo -e "${GREEN}[3/4] Ollama already installed.${NC}"
fi

# 4. Pull Default Model
echo -e "${GREEN}[4/4] Pulling default model (llama3.2)...${NC}"
# We assume the ollama service is running. If not, we might need to start it.
# On standard install, systemd starts it automatically.
if systemctl is-active --quiet ollama; then
    ollama pull llama3.2
    echo "Pulling embedding model..."
    ollama pull nomic-embed-text
else
    echo "Ollama service is not running. Attempting to start..."
    sudo systemctl start ollama
    sleep 5
    ollama pull llama3.2
    ollama pull nomic-embed-text
fi

echo -e "${GREEN}Setup Complete!${NC}"
echo "Next steps:"
echo "1. Create your .env file from .env.example"
echo "2. Run 'docker compose up --build'"
