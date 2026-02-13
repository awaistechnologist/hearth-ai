#!/bin/bash
# Simply run ./deploy.sh to push code and rebuild the bot on Geekom

echo "🚀 Deploying Hearth Bot to Geekom (homeubuntu)..."

# 1. Sync Code (Exclude .git and venv if any)
rsync -av --exclude='.git' --exclude='__pycache__' ./hearth_bot awais-tahir@homeubuntu:~/hearth/

# 2. Rebuild & Restart
echo "🔄 Rebuilding Container..."
ssh awais-tahir@homeubuntu "cd ~/hearth && docker compose up -d --build hearth-bot"

echo "✅ Done!"
