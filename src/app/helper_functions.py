from flask import jsonify
from utils.utils import is_valid_future_date
from utils.aws.dynamodb import delete_current_book, put_book, get_current_book, get_cached_book_list, update_discussion_date_current_book, finish_current_book
from utils.discord_actions import create_guild_event, update_guild_event
import pytz
from datetime import time as dt_time
eastern = pytz.timezone('America/New_York')


def handle_book_select(raw_request, pending_selections, reschedule: bool):
    guild_id = raw_request.get("guild_id")
    curr_book = get_current_book(guild_id)
    # do a check to make sure there isnt a current book already
    if curr_book and not reschedule:
        return jsonify({
            "type": 4,
            "data": {
                "content": "📚 A current book has been set for this server! Please use /current to see it!",
                "flags": 64  # Ephemeral
            }
        })
    
    curr_book_title = None
    if not reschedule:
        user_id = raw_request["member"]["user"]["id"]
        custom_id = raw_request["data"]["custom_id"]

        selected_idx = int(custom_id.split("_")[-1])
        current_books_list = get_cached_book_list(guild_id=guild_id)
        selected_book = current_books_list[selected_idx]

        pending_selections.setdefault(guild_id, {})[user_id] = selected_book
        curr_book_title = selected_book['volumeInfo']['title']
    else:
        curr_book_title = curr_book.get("title", "Unknown Title")
    
    # Truncate book title if too long for Discord modal title (max 45 chars)
    max_title_len = 45
    prefix = "Reschedule Discussion for " if reschedule else "Plan Discussion for "
    allowed_book_len = max_title_len - len(prefix) - 3  # 3 for "..."
    display_title = curr_book_title[:allowed_book_len] + ("..." if len(curr_book_title) > allowed_book_len else "")

    modal = {
        "custom_id": f"select_schedule_{'reschedule' if reschedule else 'new'}",
        "title": f"{prefix}{display_title}",
        "components": [
            {
                "type": 1,  # Action row
                "components": [
                    {
                        "type": 4,  # Text input
                        "custom_id": "discussion_date",
                        "style": 1,
                        "label": f"{'New Discussion Date | Previous: ' if reschedule else 'Discussion Date | '}{curr_book.get('discussion_date', 'TBD') if reschedule else '(MM-DD-YYYY)'}",
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

def handle_schedule_select(raw_request, pending_selections, reschedule):
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

    # Validate discussion date for both new selections and rescheduling
    if not is_valid_future_date(discussion_date):
        return jsonify({
            "type": 4,
            "data": {
                "content": "❌ Please enter a valid future date in MM-DD-YYYY format.",
                "flags": 64  # Ephemeral message
            }
        })

    # Compose description with pages/chapters and EST time
    def make_event_description(title, pages_or_chapters):
        desc = f"Discussion for {title}."
        if pages_or_chapters:
            desc += f" Reading: {pages_or_chapters}."
        return desc

    # Convert discussion_date to EST and UTC for Discord event
    from datetime import datetime
    dt = datetime.strptime(discussion_date, "%m-%d-%Y")
    # Default to 7:00 PM EST
    dt_est = eastern.localize(datetime.combine(dt.date(), dt_time(19, 0)))
    est_time_str = dt_est.strftime("%m-%d-%Y %I:%M %p EST")
    dt_utc = dt_est.astimezone(pytz.utc)
    start_time_iso = dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

    if reschedule:
        # Get current book to fetch event ID
        curr_book = get_current_book(guild_id)
        discord_event_id = curr_book.get("discord_event_id")
        event_updated = False
        if discord_event_id:
            try:
                curr_title = curr_book.get('title', 'Book')
                curr_pages = pages_or_chapters
                update_guild_event(
                    guild_id,
                    discord_event_id,
                    scheduled_start_time=start_time_iso,
                    description=make_event_description(curr_title, curr_pages)
                )
                event_updated = True
            except Exception as e:
                print(f"Failed to update Discord event: {e}")
        response = update_discussion_date_current_book(guild_id, discussion_date, curr_pages, discord_event_id=discord_event_id if event_updated else None)
        return jsonify({
            "type": 4,
            "data": {
                "content": f"✅ {response.get('title', 'Unknown Title')} has been rescheduled from {response.get('discussion_date', 'TBD')} to {discussion_date} and from {response.get('set_page_or_chapter', 'TBD')} to {curr_pages}!"
            }
        })
    
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

    # Create Discord event for the new meeting
    event_id = None
    try:
        event_desc = make_event_description(selected_book['volumeInfo']['title'], pages_or_chapters)
        event = create_guild_event(
            guild_id,
            name=f"Book Club: {selected_book['volumeInfo']['title']}",
            description=event_desc,
            start_time=start_time_iso
        )
        event_id = event.get("id")
    except Exception as e:
        print(f"Failed to create Discord event: {e}")

    # Save to DynamoDB (with event ID if available)
    put_book(guild_id, user_id, selected_book, discussion_date, pages_or_chapters, discord_event_id=event_id)

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


def handle_confirm_book_delete(guild_id, user_id, role_ids):
    if not any(role_id == '1393651462558449815' for role_id in role_ids):
        return jsonify({
            "type": 4,
            "data": {
                "content": f"❌ Sorry <@{user_id}>, You don't have permission to delete the current book.",
                "flags": 64  # Ephemeral
            }
        })

    return jsonify({
        "type": 4,
        "data": {
            "content": "⚠️ Are you sure you want to delete the current book?",
            "flags": 64,  # Ephemeral
            "components": [
                {
                    "type": 1,  # Action row
                    "components": [
                        {
                            "type": 2,  # Button
                            "style": 2,  # Secondary (gray)
                            "label": "No",
                            "custom_id": f"delete_confirm_no_{guild_id}"
                        },
                        {
                            "type": 2,  # Button
                            "style": 4,  # Danger (red)
                            "label": "Yes",
                            "custom_id": f"delete_confirm_yes_{guild_id}"
                        }
                    ]
                }
            ]
        }
    })

def handle_book_delete(guild_id, user_id, role_ids, confirmation):

    if not any(role_id == '1393651462558449815' for role_id in role_ids):
        return jsonify({
            "type": 4,
            "data": {
                "content": f"❌ Sorry <@{user_id}>, You don't have permission to delete the current book.",
                "flags": 64  # Ephemeral
            }
        })
    # If confirmation is True, proceed with deletion
    if confirmation:
        response = delete_current_book(guild_id)
        if not response:
            return jsonify({
                "type": 4,
                "data": {
                    "content": "❗ No current book found to delete.",
                    "flags": 64  # Ephemeral
                }
            })
        return jsonify({
            "type": 4,
            "data": {
                "content": f"✅ Book {response['title']} by {response['authors']} has been removed from current reading!",
            }
        })
    else:
        return jsonify({
            "type": 4,
            "data": {
                "content": f"❌ Cancelled deletion of the current book.",
                "flags": 64  # Ephemeral
            }
        })


def handle_finish_book(guild_id, user_id, role_ids):
    if not any(role_id == '1393651462558449815' for role_id in role_ids):
        return jsonify({
            "type": 4,
            "data": {
                "content": f"❌ Sorry <@{user_id}>, You don't have permission to finish the current book.",
                "flags": 64  # Ephemeral
            }
        })

    response = finish_current_book(guild_id)
    if not response:
        return jsonify({
            "type": 4,
            "data": {
                "content": "❗ No current book found to finish.",
                "flags": 64  # Ephemeral
            }
        })
    return jsonify({
        "type": 4,
        "data": {
            "content": f"✅ Book {response['title']} by {response['authors']} has been finished! Congratulations! 🎉",
        }
    })