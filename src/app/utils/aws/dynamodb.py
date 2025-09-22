import boto3 # type: ignore
import os
from datetime import datetime, timezone, date
import time
from typing import Any
import json

dynamodb = boto3.resource("dynamodb")

current_book_table_name = os.environ["CURRENT_BOOK_TABLE"]
history_table_name = os.environ["HISTORY_BOOK_TABLE"]
cache_table_name = os.environ["CACHE_TABLE"]

# tables
current_book_table = dynamodb.Table(current_book_table_name)
history_book_table = dynamodb.Table(history_table_name)
cache_table = dynamodb.Table(cache_table_name)


# @TODO: Make this function type safe
def put_book(
        guild_id: str, 
        user_id: str, 
        selected_book: dict[str, dict], 
        discussion_date: datetime,
        discussion_time: str,
        pages_or_chapters,
        discord_event_id: str = None
    ) -> None:

    if not all([guild_id, user_id, selected_book, discussion_date, discussion_time, pages_or_chapters]):
        msg = f"Book information missing. Please enter valid book info."
        raise Exception(msg)

    try:
        # Extract info from selected_book (adjust fields as per your data)
        volume_info = selected_book.get("volumeInfo", {})
        title = volume_info.get("title", "Unknown Title")
        authors = ", ".join(volume_info.get("authors", ["Unknown Author"]))
        isbn_list = volume_info.get("industryIdentifiers", [])
        isbn_13 = next((id["identifier"] for id in isbn_list if id["type"] == "ISBN_13"), None)
        isbn_10 = next((id["identifier"] for id in isbn_list if id["type"] == "ISBN_10"), None)
        isbn = isbn_13 or isbn_10 or "N/A"

        # Create a unique primary key for current selection (e.g., "CURRENT_BOOK")

        # Put item into DynamoDB table
        item = {
            "guild_id": guild_id,  # Partition key (table schema dependent)
            "discussion_date": discussion_date,
            "discussion_time": discussion_time,
            "title": title,
            "authors": authors,
            "isbn": isbn,
            "set_by_user": user_id,
            "set_page_or_chapter": pages_or_chapters,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if discord_event_id:
            item["discord_event_id"] = discord_event_id
        current_book_table.put_item(Item=item)
    except Exception as e:
        msg = f"failed to put book {selected_book} into table. {e}"
        raise Exception(msg)

# Get the current book being read as well the next scheduled date
def get_current_book(guild_id: str) -> dict[str, Any]:
    if not guild_id:
        raise Exception("guild_id missing.")
    
    response = current_book_table.get_item(Key={"guild_id": guild_id})
    return response.get("Item", {})

# delete the current book in case the server does not want to read it
def delete_current_book(guild_id: str) -> dict:
    if not guild_id:
        raise Exception("guild_id missing.")

    try:
        response = current_book_table.delete_item(
            Key={"guild_id": guild_id},
            ReturnValues="ALL_OLD"  # returns the deleted item attributes if it existed
        )
        # Return the old item if it was deleted, or None if no item found
        return response.get("Attributes")
    except Exception as e:
        raise Exception(f"Failed to delete current book. {e}")


# update the schedule of the book
def update_discussion_date_current_book(guild_id: str, discussion_date: str, discussion_time: str, pages_or_chapters: str, discord_event_id: str = None) -> dict:
    if not guild_id or not discussion_date or not discussion_time or not pages_or_chapters:
        raise Exception("Guild_ID, a new discussion date, discussion time, and pages or chapters are required.")

    try:
        update_expr = "SET #d = :new_date, #t = :updated_at, #p = :pages, #dt = :discussion_time"
        expr_attr_names = {
            "#d": "discussion_date",
            "#t": "timestamp",
            "#p": "set_page_or_chapter",
            "#dt": "discussion_time"
        }
        expr_attr_values = {
            ":new_date": discussion_date,
            ":updated_at": datetime.now(timezone.utc).isoformat(),
            ":pages": pages_or_chapters,
            ":discussion_time": discussion_time
        }
        if discord_event_id:
            update_expr += ", #e = :event_id"
            expr_attr_names["#e"] = "discord_event_id"
            expr_attr_values[":event_id"] = discord_event_id
        response = current_book_table.update_item(
            Key={"guild_id": guild_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_attr_names,
            ExpressionAttributeValues=expr_attr_values,
            ReturnValues="ALL_OLD"  # returns the old item attributes
        )
        return response.get("Attributes", {})
    except Exception as e:
        raise Exception(f"Failed to update discussion date for guild {guild_id}. {e}")

def finish_current_book(guild_id: str) -> None:    
    if not guild_id:
        raise Exception("guild_id is required to finish the current book.")

    # Get the current book
    current_book = get_current_book(guild_id)
    
    if not current_book:
        raise Exception(f"No current book found for guild {guild_id}.")

    # Move to history table
    history_book_table.put_item(Item=current_book)

    # Delete from current book table
    return delete_current_book(guild_id)

# CACHING LOGIC
def cache_book_list(
        guild_id: str, 
        book_list: list[str], 
        ttl: int = 15*60
    ) -> None:
    """
    Puts the book_list into DynamoDB with a TTL of 15 mins
    
    Input
        guild_id: server id
        book_list: list of books returned by Google books API

    Ouptut:
        None

    Raises:
        Exception when either guild_id or book_list is None
        Exception when put_item action fails
    """

    if not guild_id or not book_list:
        msg = f"Invalid guild_id or book_list entered."
        raise Exception(msg)
    
    expire_timestamp = int(time.time()) + ttl
    
    payload = {
        "guild_id": guild_id,
        "book_list": json.dumps(book_list),
        "ttl": expire_timestamp
    }

    try:
        cache_table.put_item(
            Item=payload,
        )
    except Exception as e:
        msg = f"Failed to put item into table. {e}"
        raise Exception(msg)

def get_cached_book_list(guild_id: str) -> Any:
    """
    Gets book list from the dynamodb cache

    Input:
        guild_id: server id

    Output:
        book_list: the cached book list
    
    Raises:
        Exception when invalid guild_id is entered
        Exception when the retrieval fails
    """
    
    if not guild_id:
        msg = f"Invalid guild_id entered."
        raise Exception(msg)

    try:
        response = cache_table.get_item(
            Key={
                "guild_id": guild_id
            }
        )
        
        print("[DEBUG]", response)

        if "Item" in response:
            return json.loads(response["Item"]["book_list"])
        
        # if no item found
        raise
    except Exception as e:
        msg = f"Failed to retrieve item from cache table for key {guild_id}. {e}"
        raise Exception(msg)