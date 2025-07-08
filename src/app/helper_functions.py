from flask import jsonify
from utils.utils import is_valid_future_date
from utils.aws.dynamodb import put_book, get_current_book, get_cached_book_list


def handle_book_select(raw_request, pending_selections):
    guild_id = raw_request.get("guild_id")
    # do a check to make sure there isnt a current book already
    if get_current_book(guild_id):
        return jsonify({
            "type": 4,
            "data": {
                "content": "📚 A current book has been set for this server! Please use /current to see it!",
                "flags": 64  # Ephemeral
            }
        })


    user_id = raw_request["member"]["user"]["id"]
    custom_id = raw_request["data"]["custom_id"]

    selected_idx = int(custom_id.split("_")[-1])
    current_books_list = get_cached_book_list(guild_id=guild_id)
    selected_book = current_books_list[selected_idx]

    pending_selections.setdefault(guild_id, {})[user_id] = selected_book
    print(f"pending selections BOOKS LIST: ", pending_selections)

    modal = {
        "custom_id": "select_schedule",
        "title": "Plan Discussion",
        "components": [
            {
                "type": 1,  # Action row
                "components": [
                    {
                        "type": 4,  # Text input
                        "custom_id": "discussion_date",
                        "style": 1,
                        "label": "Discussion Date (MM-DD-YYYY)",
                        "min_length": 10,
                        "max_length": 10,
                        "placeholder": "03-28-2003",
                        "required": True
                    }
                ]
            },
            {
                "type": 1,  # Another action row
                "components": [
                    {
                        "type": 4,  # Text input
                        "custom_id": "pages_or_chapters",
                        "style": 1,
                        "label": "Pages or Chapters to Read",
                        "min_length": 1,
                        "max_length": 100,
                        "placeholder": "e.g. Chapters 1-3 or Pages 1-50",
                        "required": True
                    }
                ]
            }
        ]
    }

    return jsonify({
        "type": 9,
        "data": modal
    })

def handle_schedule_select(raw_request, pending_selections):
    user_id = raw_request["member"]["user"]["id"]
    guild_id = raw_request.get("guild_id")
    
    discussion_date = None
    pages_or_chapters = None

    # Extract date and reading plan from modal inputs
    for action_row in raw_request["data"]["components"]:
        for component in action_row["components"]:
            if component["custom_id"] == "discussion_date":
                discussion_date = component["value"]
            elif component["custom_id"] == "pages_or_chapters":
                pages_or_chapters = component["value"]

    # Retrieve the selected book from pending selections
    selected_book = pending_selections.get(guild_id, {}).get(user_id)

    if not selected_book:
        return jsonify({
            "type": 4,
            "data": {
                "content": "❗ No book selected to save. Please try again.",
                "flags": 64
            }
        })

    # Validate discussion date
    if not is_valid_future_date(discussion_date):
        return jsonify({
            "type": 4,
            "data": {
                "content": "❌ Please enter a valid future date in MM-DD-YYYY format.",
                "flags": 64  # Ephemeral message
            }
        })

    # Save to DynamoDB
    put_book(guild_id, user_id, selected_book, discussion_date, pages_or_chapters)

    # Clean up pending selection
    pending_selections[guild_id].pop(user_id, None)
    if not pending_selections[guild_id]:  # Optional cleanup
        del pending_selections[guild_id]

    return jsonify({
        "type": 4,
        "data": {
            "content": f"✅ Book '{selected_book['volumeInfo']['title']}' scheduled for discussion on {discussion_date}!"
        }
    })

