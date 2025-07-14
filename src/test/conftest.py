import pytest
from unittest.mock import Mock, patch, MagicMock
import os

@pytest.fixture()
def mock_env_vars():
    with patch.dict(os.environ, {
        "CURRENT_BOOK_TABLE": "test_book_table",
        "CACHE_TABLE": "test_cache_table"
    }):
        yield

@pytest.fixture()
def mock_dynamodb():
    with patch("boto3.resource") as mock_resource:
        mock_table = Mock()
        mock_dynamodb = Mock()
        mock_dynamodb.Table.return_value = mock_table
        mock_resource.return_value = mock_dynamodb
        yield mock_table