from flask import Flask, jsonify, request
from mangum import Mangum
from asgiref.wsgi import WsgiToAsgi
from discord_interactions import verify_key_decorator
from helper_functions import handle_book_delete, handle_book_select, handle_schedule_select
from command_handler import command_handler
from config import DISCORD_PUBLIC_KEY, IN_DEVELOPMENT

# @TODO: Convert this to use redis instead
# pending selections
pending_selections = {}
# storing the current books being looked at
current_books_list = {}

# flask set up
app = Flask(__name__)
asgi_app = WsgiToAsgi(app)
handler = Mangum(asgi_app, lifespan="off")

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
    role_ids = raw_request["member"]["roles"]
    guild_id = raw_request.get("guild_id")
    

    # ping request == 1
    if request_type == 1:  # PING
        return jsonify({"type": 1})  # PONG

    # button request == 3
    if request_type == 3:
        custom_id = raw_request["data"]["custom_id"]
        # select book method
        if custom_id.startswith("select_book_"):
            return handle_book_select(raw_request, pending_selections)
        elif custom_id == "finish_book":
            # @TODO: Make these functions in helper_functions 
            return jsonify({"type": 4, "data": {"content": IN_DEVELOPMENT}})
        elif custom_id == "reschedule_book":
            # @TODO: Make these functions in helper_functions
            return jsonify({"type": 4, "data": {"content": IN_DEVELOPMENT}})
        elif custom_id == "delete_book":
            # @TODO: Make these functions in helper_functions
            return handle_book_delete(guild_id, user_id, role_ids)
        # default
        return jsonify({"type": 4, "data": {"content": "Unknown interaction"}})
        
    # modal request == 5
    if request_type == 5:
        custom_id = raw_request["data"]["custom_id"]
        if custom_id == "select_schedule":
            return handle_schedule_select(raw_request, pending_selections)

        # default
        return jsonify({"type": 4, "data": {"content": "Unknown interaction"}})
    


    # handle the / commands (i.e. /hello, /echo, etc...)
    return command_handler(raw_request)

# Main Method
if __name__ == "__main__":
    app.run(debug=True)
