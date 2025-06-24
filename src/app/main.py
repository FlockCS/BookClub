from flask import Flask, jsonify, request
from mangum import Mangum
from asgiref.wsgi import WsgiToAsgi
from discord_interactions import verify_key_decorator
import requests
from dynamodb import put_book
from config import DISCORD_PUBLIC_KEY, GOOGLE_BOOKS_API_URL
from utils import random_greeting


pending_selections = {}
current_books_list = {}

# flask set up
app = Flask(__name__)
asgi_app = WsgiToAsgi(app)
handler = Mangum(asgi_app)

def handle_button_click(raw_request):
    user_id = raw_request["member"]["user"]["id"]
    custom_id = raw_request["data"]["custom_id"]  # e.g. "select_book_2"

    # Extract selected book index
    selected_idx = int(custom_id.split("_")[-1])
    selected_book = current_books_list[selected_idx]  # keep this list available globally or in context

    # Store in in-memory dict
    pending_selections[user_id] = selected_book

    # Respond with modal to pick discussion date
    modal = {
      "type": 9,
      "custom_id": "select_discussion_date",
      "title": "Pick Discussion Date",
      "components": [
        {
          "type": 1,
          "components": [
            {
              "type": 4,
              "custom_id": "discussion_date",
              "style": 1,
              "label": "Discussion Date (YYYY-MM-DD)",
              "min_length": 10,
              "max_length": 10,
              "placeholder": "2025-07-01",
              "required": True
            }
          ]
        }
      ]
    }

    return jsonify({
      "type": 9,  # Modal response type
      "data": modal
    })

def handle_modal_submit(raw_request):
    user_id = raw_request["member"]["user"]["id"]
    values = raw_request["data"]["components"]
    # Extract date from modal inputs:
    discussion_date = values[0]["components"][0]["value"]

    selected_book = pending_selections.get(user_id)

    if not selected_book:
        return jsonify({
            "type": 4,
            "data": {"content": "❗ No book selected to save. Please try again."}
        })

    # Now save selected_book + discussion_date to DynamoDB (your save logic here)
    put_book(raw_request.get("guild_id"), user_id, selected_book, discussion_date)

    # Remove the pending selection
    del pending_selections[user_id]

    return jsonify({
        "type": 4,
        "data": {"content": f"✅ Book '{selected_book['volumeInfo']['title']}' scheduled for discussion on {discussion_date}!"}
    })


# post request method
@app.route("/", methods=["POST"])
async def interactions():
    print(f"👉 Request: {request.json}")
    raw_request = request.json
    return interact(raw_request)

# command handler
@verify_key_decorator(DISCORD_PUBLIC_KEY)
def interact(raw_request):    
    # @NOTE data vars from raw request that are needed
    data = raw_request["data"]
    request_type = raw_request["type"]
    user_id = raw_request["member"]["user"]["id"]
    guild_id = raw_request.get("guild_id")
    
    # ping request
    if request_type == 1:  # PING
        return jsonify({"type": 1})  # PONG

    # button request
    if request_type == 3:
        custom_id = raw_request["data"]["custom_id"]
        if custom_id.startswith("select_book_"):
            return handle_button_click(raw_request)
        
    # modal request
    if request_type == 5:
        custom_id = raw_request["data"]["custom_id"]
        if custom_id == "select_discussion_date":
            return handle_modal_submit(raw_request)

        return jsonify({"type": 4, "data": {"content": "Unknown interaction"}})
    
    # This line cannot be moved
    command_name = data["name"]
    # Hello Command
    if command_name == "hello":
        message_content = f"{random_greeting()} <@{user_id}>!"

    elif command_name == "echo":
        original_message = data["options"][0]["value"]
        message_content = f"Echoing: {original_message}"

    elif command_name == "search":
        # building a dictionary to obtain search values (ex: key=Title: value=Book Title, key=Author: Value: Author)
        print(data)
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
            sectionsReturn = []
            global current_books_list
            current_books_list = books  # save for button click handler
            for idx, book in enumerate(books):
                info = book["volumeInfo"]
                title = info.get("title", "No title")
                authors = ", ".join(info.get("authors", ["Unknown author"]))
                desc = info.get("description", "")
                thumbnail = info.get("imageLinks", {}).get("thumbnail")
                previewLink = info.get("previewLink", "No Link")
                industry_ids = info.get("industryIdentifiers", [])

                # Prefer ISBN-13 if available
                isbn_13 = next((id["identifier"] for id in industry_ids if id["type"] == "ISBN_13"), None)
                isbn_10 = next((id["identifier"] for id in industry_ids if id["type"] == "ISBN_10"), None)

                isbn = isbn_13 or isbn_10

                short_desc = (desc[:150] + "...") if len(desc) > 150 else desc

                section = {
                    "type": 9,
                    "components": [
                        {"type": 10, "content": f"**{idx + 1}) {title}** by {authors}"},
                        {"type": 10, "content": f"ISBN: {isbn}"},
                        {"type": 10, "content": f"Preview: {previewLink}"},
                    ]
                }
                # if short_desc:
                #     section["components"].append({
                #         "type": 10,
                #         "content": short_desc
                #     })

                if thumbnail:
                    section["accessory"] = {
                        "type": 11,
                        "media": {
                            "url": thumbnail
                        }
                    }

                sectionsReturn.append(section)
            
            
            # @TODO: Polish Button Feature to select which books the book club is reading currently and upload to DynamoDB
            button_row = {
                "type": 1,
                "components": []
            }

            for idx, book in enumerate(books[:5]):
                title = book["volumeInfo"].get("title", "Book")
                button_row["components"].append({
                    "type": 2,
                    "label": f"{idx+1}",
                    "style": 1,
                    "custom_id": f"select_book_{idx}"
            })
            sectionsReturn.append(button_row)
            
            
            return jsonify({
                "type": 4,
                "data": {
                    "flags": 32768,
                    "components": sectionsReturn
                }
            })
            
    else:
        message_content = "Unknown command."
    
    return jsonify({
        "type": 4,
        "data": {"content": message_content},
    })

# Main Method
if __name__ == "__main__":
    app.run(debug=True)
