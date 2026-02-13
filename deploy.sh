#!/bin/bash
# Simply run ./deploy.sh to push code and rebuild the bot on Geekom

# Configuration
TARGET_HOST=${HEARTH_HOST:-"homeubuntu"}
TARGET_USER=${HEARTH_USER:-"awais-tahir"}
TARGET_PATH=${HEARTH_PATH:-"~/hearth"}

echo "🚀 Deploying Hearth Bot to ${TARGET_HOST}..."

# 1. Sync Code (Exclude .git and venv if any)
rsync -av --exclude='.git' --exclude='__pycache__' ./hearth_bot "${TARGET_USER}@${TARGET_HOST}:${TARGET_PATH}/"

# 2. Rebuild & Restart
echo "🔄 Rebuilding Container..."
ssh "${TARGET_USER}@${TARGET_HOST}" "cd ${TARGET_PATH} && docker compose up -d --build hearth-bot"

echo "✅ Done!"
