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
    Delete a Discord scheduled event if it exists.
    Returns True if deleted, False if not found, raises for other errors.
    """
    url = f"{DISCORD_API_BASE}/guilds/{guild_id}/scheduled-events/{event_id}"
    response = requests.delete(url, headers=HEADERS)
    if response.status_code == 404:
        # Event does not exist, nothing to delete
        return False
    response.raise_for_status()
    return response.status_code == 204  # Discord returns 204 No Content on successful delete

def create_discussion_thread(guild_id, thread_name, book_title, section):
    """
    Create a thread in the specified channel for book discussion.
    The thread name and first message follow a custom format.
    """
    channel_id = get_megathreads_channel_id(guild_id)

    url = f"{DISCORD_API_BASE}/channels/{channel_id}/threads"
    thread_name = f"Week {1} - {book_title}"
    payload = {
        "name": thread_name,
        "type": 11  # Public thread
        # No auto_archive_duration field
    }
    headers = {
        "Authorization": f"Bot {BOT_TOKEN}",
        "Content-Type": "application/json"
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    thread = response.json()

    # Send the first message in the thread with the custom description
    message_content = (
        f"Week {1}\n"
        f"Book: {book_title}\n"
        f"Section: {section}\n"
        "Happy Reading 📖"
    )
    thread_id = thread["id"]
    message_url = f"{DISCORD_API_BASE}/channels/{thread_id}/messages"
    message_payload = {"content": message_content}
    message_response = requests.post(message_url, headers=headers, json=message_payload)
    message_response.raise_for_status()
    return thread

def get_megathreads_channel_id(guild_id):
    """
    Fetches the ID of the 'megathreads' text channel for the given guild.
    Returns None if not found.
    """
    url = f"{DISCORD_API_BASE}/guilds/{guild_id}/channels"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    channels = response.json()
    for channel in channels:
        # type 0 = text channel
        if channel["type"] == 0 and channel["name"].lower() == "megathreads":
            return channel["id"]
    return None