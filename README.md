# Hearth Family AI 🧠

Hearth is a local, privacy-focused AI assistant for your home. It integrates Home Assistant, Ollama (Llama 3.2), and a custom Telegram Bot with long-term memory (ChromaDB) and internet search capabilities.

## Features
- **Local Intelligence**: Runs on Llama 3.2 (3B/8B) via Ollama. No cloud dependencies (unless configured).
- **Home Control**: Integrates with Home Assistant to control devices and read sensor data.
- **Long-Term Memory**: Remembers family facts (wifi passwords, preferences) using Vector RAG (ChromaDB).
- **Internet Aware**: Can search the web for real-time info (with user permission).
- **Secure**: Strict user authorization flow.

## Prerequisites
- Docker & Docker Compose
- Ollama (running locally or on network) with `llama3.2` model pulled.
- Home Assistant (running or accessible).
- **Telegram Bot Token**: Create one via [@BotFather](https://t.me/BotFather) on Telegram.
  1.  Send `/newbot`.
  2.  Name it (e.g., "My Home AI").
  3.  Get the HTTP API Token.

## Quick Start

1. **Clone the Repo**
   ```bash
   git clone https://github.com/yourusername/hearth.git
   cd hearth
   ```

2. **Configure Secrets**
   Copy the example and fill in your details:
   ```bash
   cp .env.example .secrets
   nano .secrets
   ```
   *Get your `HASS_TOKEN` from Home Assistant Profile -> Long-Lived Access Tokens.*

3. **Install Dependencies (Ollama)**
   Ensure Ollama is running and has the model:
   ```bash
   # If running Ollama locally
   ollama pull llama3.2
   ollama pull nomic-embed-text # Optional, if using ollama for embeddings
   ```
   *Note: Hearth uses `sentence-transformers` (all-MiniLM-L6-v2) by default for memory, which downloads automatically.*

4. **Launch**
   ```bash
   docker compose up -d --build
   ```

5. **Initialize**
   - Open your Telegram Bot.
   - Send `/start`.
   - Send `/id` to get your User ID.
   - Ensure `ADMIN_ID` in `.secrets` matches your ID. The admin is auto-approved on restart.
   - Admin can use `/permit <user_id>` to allow other family members.

## Architecture
- **hearth_bot/**: The main Python application (Telegram Bot + Memory Logic + Ollama Client). This is the brain.
- **ha_components/**: Custom Home Assistant integration (optional) for tighter LLM coupling.
- **ha_config/**: Example configuration for Home Assistant (Mercedes component etc).
- **core/**: (Removed).

## License
MIT License.
