from flask import json, jsonify
import requests
from config import GOOGLE_BOOKS_API_URL, IN_DEVELOPMENT, DICTIONARY_API_URL
from utils.aws.dynamodb import get_current_book, cache_book_list, get_cached_book_list
from utils.utils import random_greeting

def command_handler(raw_request):
    """
    Handles incoming Discord slash command interactions (type 1).

    Args:
        raw_request (dict): The raw interaction payload from Discord.

    Returns:
        dict: A JSON-serializable response conforming to Discord's interaction response format.
    """
    # vars needed for each command
    data = raw_request["data"]
    command_name = raw_request["data"]["name"]
    user_id = raw_request["member"]["user"]["id"]
    guild_id = raw_request.get("guild_id")

     # Hello Command
    if command_name == "hello":
        message_content = f"{random_greeting()} <@{user_id}>!"

    elif command_name == "echo":
        original_message = data["options"][0]["value"]
        message_content = f"Echoing: {original_message}"
    
    elif command_name == "define":
        define_word = data["options"][0]["value"]
        URL = f"{DICTIONARY_API_URL}{define_word}"
        response = requests.get(url=URL)

        # Check if response is OK and JSON is valid
        if not response.ok:
            message_content = f"❌ Could not find definitions for **{define_word}**"
            return jsonify({
                "type": 4,
                "data": {"content": message_content}
            })

        data = response.json()
        if not data or not isinstance(data, list) or "meanings" not in data[0]:
            message_content = f"❌ Could not find definitions for **{define_word}**"
            return jsonify({
                "type": 4,
                "data": {"content": message_content}
            })

        # Organize definitions
        definitions_by_pos = {}
        for meaning in data[0]["meanings"]:
            pos = meaning.get("partOfSpeech", "Unknown").capitalize()
            definitions = [entry.get("definition", "") for entry in meaning.get("definitions", [])]
            definitions_by_pos.setdefault(pos, []).extend(definitions)

        # Optional: limit definitions per part of speech
        max_defs_per_pos = 3
        for pos in definitions_by_pos:
            definitions_by_pos[pos] = definitions_by_pos[pos][:max_defs_per_pos]

        # Convert to embed fields
        fields = []
        for part_of_speech, definitions in definitions_by_pos.items():
            value = "\n".join([f"{idx + 1}. {definition}" for idx, definition in enumerate(definitions)])
            fields.append({
                "name": part_of_speech,
                "value": value if value else "*No definitions available.*",
                "inline": False
            })

        embed = {
            "title": f"Definitions for _{define_word}_",
            "fields": fields,
            "color": 0x5865F2  # Discord blurple
        }

        return jsonify({
            "type": 4,
            "data": {
                "embeds": [embed],
                "flags": 64  # Optional: make ephemeral
            }
        })

    elif command_name == "current":
        book = get_current_book(guild_id)
        # 1️⃣ Nothing in DynamoDB yet
        if book is None:
            return jsonify({
                "type": 4,
                "data": {
                    "content": "📚 No current book has been set for this server. Use `/search` to pick one!",
                    "flags": 64        # Ephemeral
                }
            })

        # 2️⃣ Pull the fields we stored
        title            = book.get("title", "Unknown Title")
        authors          = book.get("authors", "Unknown Author")
        isbn             = book.get("isbn", "N/A")
        discussion_date  = book.get("discussion_date", "TBD")
        pages            = book.get("set_page_or_chapter", "—")

        # Optional: if you stored a cover URL in DynamoDB
        thumbnail_url    = book.get("thumbnail")      # may be None
        embed = {
            "title": title,
            "description": f"Author: {authors}\n"
                        f"ISBN: {isbn}\n"
                        f"Discussion: {discussion_date}\n"
                        f"Pages / chapter: {pages}",
        }
        if thumbnail_url:
            embed["thumbnail"] = {"url": thumbnail_url}

        # ─── action‑row with two buttons ────────────────────────
        button_row = {
            "type": 1,           # ACTION_ROW
            "components": [
                {
                    "type": 2,             # BUTTON
                    "label": "Reschedule",
                    "style": 1,            # Primary
                    "custom_id": "reschedule_book"
                },
                {
                    "type": 2,
                    "label": "Finish",
                    "style": 1,
                    "custom_id": "finish_book"
                }
            ]
        }

        return jsonify({
            "type": 4,  # CHANNEL_MESSAGE_WITH_SOURCE
            "data": {
                "embeds": [embed],          # rich message with book info
                "components": [button_row]  # action row with buttons
            }
        })

        
    elif command_name == "search":
        # building a dictionary to obtain search values (ex: key=Title: value=Book Title, key=Author: Value: Author)
        query_options = {opt["name"]: opt["value"] for opt in data.get("options", [])}

        # if no queries are present, then return an error
        if not any(k in query_options for k in ["title", "author", "publisher", "isbn"]):
            return jsonify({
                "type": 4,
                "data": {
                    "content": "❗Please provide at least one search option (e.g. Title, Author, Publisher, or ISBN)."
                }
            })

        # Construct query params based on whats provided to search
        query_params = []

        if "title" in query_options:
            query_params.append(f"intitle:{query_options['title']}")
        if "author" in query_options:
            query_params.append(f"inauthor:{query_options['author']}")
        if "publisher" in query_options:
            query_params.append(f"inpublisher:{query_options['publisher']}")
        if "isbn" in query_options:
            query_params.append(f"isbn:{query_options['isbn']}")

        # Final Query Response to send to URL
        final_query = "+".join(query_params)

        response = requests.get(GOOGLE_BOOKS_API_URL, params={
            "q": final_query,
            "maxResults": 5,
        })

        books = response.json().get("items", [])

        if not books:
            message_content = f"No books found for '{query_options}'."
        else:
            # cache the book list to use later
            # current_books_list[guild_id] = books  # save for button click handler
            cache_book_list(guild_id=guild_id, book_list=books, ttl=60)
            
            embeds = []
            for idx, book in enumerate(books[:5]):
                info = book["volumeInfo"]
                title = info.get("title", "No Title")
                authors = ", ".join(info.get("authors", ["Unknown Author"]))
                isbn = next((i["identifier"] for i in info.get("industryIdentifiers", []) if i["type"] == "ISBN_13"), "N/A")
                preview = info.get("previewLink", None)
                thumbnail = info.get("imageLinks", {}).get("thumbnail", None)
                description = info.get("description", "")
                short_desc = (description[:150] + "...") if len(description) > 150 else description

                embed = {
                    "title": f"{idx+1}) {title}",
                    "description": f"By: {authors}\nISBN: {isbn}",
                    "url": preview,
                }
                if thumbnail:
                    embed["thumbnail"] = {"url": thumbnail}
                embeds.append(embed)

            buttons = [{
                "type": 2,
                "label": str(i+1),
                "style": 1,
                "custom_id": f"select_book_{i}"
            } for i in range(len(books[:5]))]

            return jsonify({
                "type": 4,
                "data": {
                    "embeds": embeds,
                    "components": [{
                        "type": 1,  # Action Row
                        "components": buttons
                    }],
                }
            })

            
    else:
        message_content = "Unknown command."
    
    return jsonify({
        "type": 4,
        "data": {"content": message_content},
    })


