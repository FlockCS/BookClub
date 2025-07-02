import boto3 # type: ignore
import os
from datetime import datetime, timezone, date

def test_function():
    session = boto3.session.Session()
    print(session.get_available_resources())