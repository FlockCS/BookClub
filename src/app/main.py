import os
from flask import Flask, jsonify, request
from mangum import Mangum
from asgiref.wsgi import WsgiToAsgi
from discord_interactions import verify_key_decorator
import requests

DISCORD_PUBLIC_KEY = os.environ.get("DISCORD_PUBLIC_KEY")

app = Flask(__name__)
asgi_app = WsgiToAsgi(app)
handler = Mangum(asgi_app)

GOOGLE_BOOKS_API_URL = "https://www.googleapis.com/books/v1/volumes"

@app.route("/", methods=["POST"])
async def interactions():
    print(f"👉 Request: {request.json}")
    raw_request = request.json
    return interact(raw_request)


@verify_key_decorator(DISCORD_PUBLIC_KEY)
def interact(raw_request):
    if raw_request["type"] == 1:  # PING
        return jsonify({"type": 1})  # PONG

    data = raw_request["data"]
    command_name = data["name"]

    if command_name == "hello":
        message_content = "Hello there!"

    elif command_name == "echo":
        original_message = data["options"][0]["value"]
        message_content = f"Echoing: {original_message}"

    elif command_name == "search":
        book_name = data["options"][0]["value"]

        # Query the Google Books API
        params = {
            "q": f"intitle:{book_name}",
            "maxResults": 5  # Limit to top 5 results
        }
        response = requests.get(GOOGLE_BOOKS_API_URL, params=params)
        books = response.json().get("items", [])

        if not books:
            message_content = f"No books found for '{book_name}'."
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


if __name__ == "__main__":
    app.run(debug=True)
