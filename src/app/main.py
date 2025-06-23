import os
from flask import Flask, jsonify, request
from mangum import Mangum
from asgiref.wsgi import WsgiToAsgi
from discord_interactions import verify_key_decorator
import requests
import random

# vars
DISCORD_PUBLIC_KEY = os.environ.get("DISCORD_PUBLIC_KEY")
GOOGLE_BOOKS_API_URL = "https://www.googleapis.com/books/v1/volumes"
greetings = [
    "Hello there!",
    "Hi!",
    "Good to see you!",
    "Greetings!",
    "Hey, how are you?",
    "Nice to meet you!",
    "Hello, friend!",
    "Hi, hope you’re doing well!",
]
emojis = ["👋", "😊", "🙌", "🌟", "🤗", "😄", "✨", "😎", "😁"]

# flask set up
app = Flask(__name__)
asgi_app = WsgiToAsgi(app)
handler = Mangum(asgi_app)

# post request method
@app.route("/", methods=["POST"])
async def interactions():
    print(f"👉 Request: {request.json}")
    raw_request = request.json
    return interact(raw_request)

# command handler
@verify_key_decorator(DISCORD_PUBLIC_KEY)
def interact(raw_request):
    if raw_request["type"] == 1:  # PING
        return jsonify({"type": 1})  # PONG
    
    # data vars from raw request
    data = raw_request["data"]
    user_id = raw_request["member"]["user"]["id"]
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

            for book in books:
                info = book["volumeInfo"]
                title = info.get("title", "No title")
                authors = ", ".join(info.get("authors", ["Unknown author"]))
                desc = info.get("description", "")
                thumbnail = info.get("imageLinks", {}).get("thumbnail")

                short_desc = (desc[:150] + "...") if len(desc) > 150 else desc

                section = {
                    "type": 9,
                    "components": [
                        {"type": 10, "content": f"**{title}** by {authors}"},
                    ]
                }
                if short_desc:
                    section["components"].append({
                        "type": 10,
                        "content": short_desc
                    })

                if thumbnail:
                    section["accessory"] = {
                        "type": 11,
                        "media": {
                            "url": thumbnail
                        }
                    }

                sectionsReturn.append(section)
            
            ''' 
            @TODO: Polish Button Feature to select which books the book club is reading currently and upload to DynamoDB
            button_row = {
                "type": 1,
                "components": []
            }

            for idx, book in enumerate(books[:5]):
                title = book["volumeInfo"].get("title", "Book")
                button_row["components"].append({
                    "type": 2,
                    "label": f"Select {idx+1}",
                    "style": 1,
                    "custom_id": f"select_book_{idx}"
            })
            sectionsReturn.append(button_row)
            '''
            
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

# Random Greeting generator
def random_greeting():
    message = random.choice(greetings)
    emoji = random.choice(emojis)
    return f"{message} {emoji}"

# Main Method
if __name__ == "__main__":
    app.run(debug=True)
