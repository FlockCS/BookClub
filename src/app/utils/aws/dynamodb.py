import boto3 # type: ignore
import os
from datetime import datetime, timezone, date
import time
from typing import Any
import json

dynamodb = boto3.resource("dynamodb")

book_table_name = os.environ["BOOK_TABLE"]
cache_table_name = os.environ["CACHE_TABLE"]

# tables
book_table = dynamodb.Table(book_table_name)
cache_table = dynamodb.Table(cache_table_name)


# @TODO: Make this function type safe
def put_book(
        guild_id: str, 
        user_id: str, 
        selected_book: dict[str, dict], 
        discussion_date: datetime, 
        pages_or_chapters
    ) -> None:

    if not all([guild_id, user_id, selected_book, discussion_date, pages_or_chapters]):
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
        book_table.put_item(
            Item={
                "guild_id": guild_id,  # Partition key (table schema dependent)
                "discussion_date": discussion_date,
                "title": title,
                "authors": authors,
                "isbn": isbn,
                "set_by_user": user_id,
                "set_page_or_chapter": pages_or_chapters,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
    except Exception as e:
        msg = f"failed to put book {selected_book} into table. {e}"
        raise Exception(msg)

# Get the current book being read as well the next scheduled date
def get_current_book(guild_id: str) -> dict[str, Any]:
    if not guild_id:
        msg = f"guild_id missing."
        raise Exception(msg)
    
    response = book_table.get_item(Key={"guild_id": guild_id})

    if "Item" not in response:
        msg = f"Failed to get book from table"
        raise Exception(msg)

    return response.get("Item")


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