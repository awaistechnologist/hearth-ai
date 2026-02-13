---
description: Hearth Architecture Overview & Maintenance Guide
---

# 🏟️ Hearth Architecture & Maintenance

This document explains how the Hearth system fits together on your Raspberry Pi (or Geekom) and how to manage it.

## 1. System Architecture
The system runs on **Three Separate Layers**. They are independent and talk via Network APIs.

```mermaid
graph TD
    User((User)) -->|Telegram| Bot[Hearth Bot \n(Docker Container)]
    
    subgraph "Raspberry Pi / Host OS"
        Bot -->|HTTP :8123| HA[Home Assistant \n(Docker Container)]
        Bot -->|HTTP :11434| AI[Ollama / Generic AI \n(Native Service)]
        
        HA -->|Zigbee/WiFi| Devices[Lights/Sensors]
    end
```

### The Key Separation
*   **Home Assistant**: Only handles **Devices** and **State**. It does NOT know about the AI. It just exposes an API.
*   **Hearth Bot (This Repo)**: The **Brain**. It lives in its own Docker container. It queries Home Assistant ("Is the door locked?") and talks to Ollama or Gemini ("Summarize this").
*   **Ollama**: The **Muscle**. It runs natively on the metal for max GPU speed. It doesn't know about Telegram or Home Assistant.

## 2. Directory Structure (On the Pi)
All files live in `~/hearth`.

*   `~/hearth/docker-compose.yml`: Defines the Bot and HA services.
*   `~/hearth/.secrets`: **Private** keys (Telegram Token, HA Token). Git-ignored.
*   `~/hearth/hearth_bot/`: The Python source code for the bot.

## 3. Maintenance Cheatsheet

### 🔍 Logging & Status
*   **Check Bot Logs**:
    ```bash
    ssh awais@homepi "docker logs hearth_bot -f --tail 50"
    ```
*   **Check AI Response (Interactive)**:
    Only one Llama instance can run at a time! Ensure no background `ollama run` sessions are open if using local AI.

### 🔄 Updating the Code (The Golden Rule)
Because the Bot runs in Docker, **changing a file on the Pi does NOT update the running bot** immediately. You must Rebuild.

1.  **Deploy Code**: Copy files from Mac to Pi.
    ```bash
    scp -r hearth_bot awais@homepi:~/hearth/
    ```
2.  **Rebuild Container** (Essential):
    ```bash
    ssh awais@homepi "cd ~/hearth && docker compose up -d --build hearth-bot"
    ```
    *   `up -d`: Detached mode (background).
    *   `--build`: Forces recompilation of the python code into the image.

### ⚙️ configuration
*   **Change AI Provider** (Gemini <-> Ollama):
    Edit `docker-compose.yml` on the Pi:
    ```yaml
    environment:
      - AI_PROVIDER=gemini  # or ollama
    ```
    Then apply: `docker compose up -d` (Rebuild not needed for config changes, just restart).

*   **Change API Keys**:
    Edit `~/.secrets` on the Pi.
    Then restart: `docker compose restart hearth-bot`
