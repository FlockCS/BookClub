import boto3 # type: ignore
import os
from datetime import datetime, timezone, date

dynamodb = boto3.resource("dynamodb")
table_name = os.environ["BOOK_TABLE"]
book_table = dynamodb.Table(table_name)


# @TODO: Make this function type safe
def put_book(guild_id, user_id, selected_book, discussion_date, pages_or_chapters):
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

# Get the current book being read as well the next scheduled date
def get_current_book(guild_id):
    response = book_table.get_item(Key={"guild_id": guild_id})
    return response.get("Item")


