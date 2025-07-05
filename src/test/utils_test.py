import pytest
import boto3
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import os

def test_put_book_into_table_success(mock_dynamodb, mock_env_vars):

    from app.utils.aws.dynamodb import put_book

    res = put_book(
        guild_id='123456',
        user_id='test_user',
        selected_book={'info' : {}},
        discussion_date=datetime.now(),
        pages_or_chapters='Pages 1-10'
    )
    assert not res

def test_put_book_into_table_fail_missing_data(mock_dynamodb, mock_env_vars):

    from app.utils.aws.dynamodb import put_book

    with pytest.raises(Exception, match=f"Book information missing. Please enter valid book info."):
        res = put_book(
            guild_id='123456',
            user_id='test_user',
            selected_book={'info' : {}},
            discussion_date=datetime.now(),
            pages_or_chapters=''
        )

@patch("app.utils.aws.dynamodb.book_table")
def test_put_book_into_table_failed_put(mock_book_table, mock_dynamodb, mock_env_vars):
    mock_book_table.put_item.side_effect = Exception("failed put")

    from app.utils.aws.dynamodb import put_book

    selected_book = {'info' : {}}

    with pytest.raises(Exception, match=f"failed to put book {selected_book} into table. failed put"):
        res = put_book(
            guild_id='123456',
            user_id='test_user',
            selected_book=selected_book,
            discussion_date=datetime.now(),
            pages_or_chapters='Pages 1-10'
        )