import aiohttp
import asyncio
import os
from dotenv import load_dotenv

# Load from .secrets if exists (for local testing)
load_dotenv(".secrets")

async def test():
    token = os.getenv("HASS_TOKEN")
    base_url = os.getenv("HASS_URL")
    
    if not token or not base_url:
        print("Missing Env Vars")
        print(f"Token: {token[:10]}...")
        print(f"URL: {base_url}")
        return

    url = f"{base_url}/api/services/scene/turn_on"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    
    print(f"Connecting to {url}...")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, headers=headers, json={"entity_id": "scene.sleep"}) as resp:
                print(f"Status: {resp.status}")
                print(await resp.text())
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test())
