import os
import requests
from datetime import datetime

DISCORD_API_BASE = "https://discord.com/api/v10"

BOT_TOKEN = os.environ.get("DISCORD_TOKEN") 

HEADERS = {
    "Authorization": f"Bot {BOT_TOKEN}",
    "Content-Type": "application/json"
}

def create_guild_event(guild_id, name, description, start_time, end_time=None, channel_id=None, location=None):
    """
    Create a Discord scheduled event in a guild.
    start_time and end_time must be ISO8601 strings (e.g., '2024-06-01T18:00:00Z')
    If channel_id is not provided, will use the General voice channel.
    """
    if channel_id is None:
        channel_id = get_general_voice_channel_id(guild_id)
    url = f"{DISCORD_API_BASE}/guilds/{guild_id}/scheduled-events"
    payload = {
        "name": name,
        "description": description,
        "scheduled_start_time": start_time,
        "entity_type": 3 if location else 2,  # 3 = external, 2 = voice
        "privacy_level": 2,  # GUILD_ONLY
    }
    if end_time:
        payload["scheduled_end_time"] = end_time
    if channel_id:
        payload["channel_id"] = channel_id
    if location:
        payload["entity_metadata"] = {"location": location}
    response = requests.post(url, headers=HEADERS, json=payload)
    response.raise_for_status()
    return response.json()

def update_guild_event(guild_id, event_id, **kwargs):
    """
    Update a Discord scheduled event. kwargs can include any updatable event fields.
    """
    url = f"{DISCORD_API_BASE}/guilds/{guild_id}/scheduled-events/{event_id}"
    response = requests.patch(url, headers=HEADERS, json=kwargs)
    response.raise_for_status()
    return response.json()

def get_general_voice_channel_id(guild_id):
    """
    Fetches the ID of the 'General' voice channel for the given guild.
    Returns None if not found.
    """
    url = f"{DISCORD_API_BASE}/guilds/{guild_id}/channels"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    channels = response.json()
    for channel in channels:
        if channel["type"] == 2 and channel["name"].lower() == "general":
            return channel["id"]
    return None

def delete_guild_event(guild_id, event_id):
    """
    Delete a Discord scheduled event.
    """
    url = f"{DISCORD_API_BASE}/guilds/{guild_id}/scheduled-events/{event_id}"
    response = requests.delete(url, headers=HEADERS)
    response.raise_for_status()
    return response.status_code == 204  # Discord returns 204 No Content on successful delete