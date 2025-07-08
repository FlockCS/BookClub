import pytest
import boto3
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
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

def test_is_valid_future_date_success():
    date_one = (datetime.now() + timedelta(days=1)).strftime("%m-%d-%Y")
    date_two = (datetime.now() + timedelta(days=10)).strftime("%m-%d-%Y")

    from app.utils.utils import is_valid_future_date

    assert is_valid_future_date(date_one) and is_valid_future_date(date_two)

def test_is_valid_future_date_failure():
    date_one = (datetime.now() - timedelta(days=1)).strftime("%m-%d-%Y")
    date_two = datetime.now().strftime("%m-%d-%Y") # should fail since its not future

    from app.utils.utils import is_valid_future_date

    assert not is_valid_future_date(date_one) and not is_valid_future_date(date_two)

def test_is_valid_future_date_type_error():

    from app.utils.utils import is_valid_future_date

    assert not is_valid_future_date("this is not a date.")