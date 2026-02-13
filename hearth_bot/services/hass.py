import aiohttp
import os
import logging
from datetime import datetime
import urllib.parse

logger = logging.getLogger(__name__)

HASS_URL = os.getenv("HASS_URL", "http://host.docker.internal:8123")
HASS_TOKEN = os.getenv("HASS_TOKEN")

HEADERS = {
    "Authorization": f"Bearer {HASS_TOKEN}",
    "Content-Type": "application/json",
}

async def get_states():
    """Fetch all states."""
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{HASS_URL}/api/states", headers=HEADERS, timeout=10) as resp:
                if resp.status == 200:
                    return await resp.json()
                return []
        except:
            return []

async def get_events_range(start_date: str, end_date: str) -> str:
    """
    Fetch events from ALL calendars for the given range.
    Uses Home Assistant API: /api/calendars/{entity_id}?start={start}&end={end}
    """
    states = await get_states()
    calendars = [s['entity_id'] for s in states if s['entity_id'].startswith('calendar.')]
    
    if not calendars:
        return "No calendars found."
    
    # Need full ISO format for API usually, but simple date often works with recent HA.
    # Let's ensure format is YYYY-MM-DD
    # start_date and end_date come from AI as YYYY-MM-DD strings.
    
    # API requires ISO with T usually? Let's try sticking T00:00:00 to start
    start_iso = f"{start_date}T00:00:00"
    end_iso = f"{end_date}T23:59:59"
    
    # URL Encode
    params = f"start={urllib.parse.quote(start_iso)}&end={urllib.parse.quote(end_iso)}"
    
    events_found = []
    
    async with aiohttp.ClientSession() as session:
        for cal_id in calendars:
            url = f"{HASS_URL}/api/calendars/{cal_id}?{params}"
            try:
                async with session.get(url, headers=HEADERS, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        # Data is list of dicts: {'summary': '...', 'start': ..., 'end': ...}
                        for event in data:
                            summary = event.get('summary', 'Busy')
                            # clean start/end which are dicts or strings
                            # usually {'dateTime': '...'} or {'date': '...'}
                            start = event.get('start', {})
                            dt = start.get('dateTime') or start.get('date') or "Unknown"
                            
                            events_found.append(f"- [{dt}] {summary} ({cal_id})")
            except Exception as e:
                logger.error(f"Error fetching {cal_id}: {e}")
                
    if not events_found:
        return f"No events found between {start_date} and {end_date}."
    
    # Sort by date
    events_found.sort()
    
    # SAFETY LIMIT: Prevent context overflow if too many events
    if len(events_found) > 50:
        events_found = events_found[:50]
        events_found.append("... (List truncated. Please refine search range.)")

    return f"Events from {start_date} to {end_date}:\n" + "\n".join(events_found)

async def get_dashboard_status() -> str:
    """
    Returns a summarized text of important devices in the house.
    Filters by useful domains (light, switch, sensor, binary_sensor, climate, cover).
    """
    states = await get_states()
    if not states:
        return "No connection to Home Assistant."

    summary = []
    useful_domains = ["light", "switch", "sensor", "binary_sensor", "climate", "cover", "lock", "vacuum"]
    
    for s in states:
        entity_id = s['entity_id']
        domain = entity_id.split('.')[0]
        if domain in useful_domains:
            name = s['attributes'].get('friendly_name', entity_id)
            state = s['state']
            unit = s['attributes'].get('unit_of_measurement', '')
            
            # Skip boring sensors unless they are critical
            is_critical = any(k in entity_id for k in ['ink', 'printer', 'lock', 'garage', 'battery', 'smoke', 'leak'])
            if state in ['unknown', 'unavailable'] and not is_critical:
                continue
                
            summary.append(f"{name} ({entity_id}): {state}{unit}")
            
    return "\n".join(summary[:2000]) # Increased limit significantly for Gemini Context


async def call_action(domain: str, service: str, entity_id: str) -> str:
    """
    Generic Service Call. e.g. light.turn_on
    """
    url = f"{HASS_URL}/api/services/{domain}/{service}"
    payload = {"entity_id": entity_id}
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, headers=HEADERS, json=payload) as resp:
                if resp.status == 200:
                    return f"success: called {domain}.{service} on {entity_id}"
                return f"failed: {resp.status}"
        except Exception as e:
            return f"error: {e}"

async def activate_scene(scene_id: str) -> bool:
    """Activates a Home Assistant Scene"""
    url = f"{HASS_URL}/api/services/scene/turn_on"
    payload = {"entity_id": scene_id}
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, headers=HEADERS, json=payload) as resp:
                return resp.status == 200
        except:
            return False

async def get_security_dashboard() -> str:
    """
    Returns a text summary of ALL potential security entities for AI analysis.
    Auto-detects: locks, covers, binary_sensors (door/lock), and sensors with 'lock'/'door' in name.
    """
    states = await get_states()
    summary = []
    
    for s in states:
        eid = s.get("entity_id", "")
        name = s.get("attributes", {}).get("friendly_name", eid)
        state = s.get("state")
        domain = eid.split(".")[0]
        
        # Generic Discovery Logic
        is_security = False
        
        if domain in ["lock", "cover", "alarm_control_panel"]:
            is_security = True
        elif domain == "binary_sensor":
            dev_class = s.get("attributes", {}).get("device_class")
            if dev_class in ["door", "garage_door", "lock", "window", "opening"]:
                is_security = True
        
        # Keyword Fallback (for weird things like sensor.mercedes_lock)
        if not is_security:
            if "lock" in eid or "door" in eid or "garage" in eid or "gate" in eid:
                is_security = True
        
        if is_security:
            summary.append(f"- {name} ({eid}): {state}")
            
    return "\n".join(summary)
