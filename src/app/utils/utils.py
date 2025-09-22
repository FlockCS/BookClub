from datetime import datetime, date
import random
import re

GREETINGS = [
    "Hello there!",
    "Hi!",
    "Good to see you!",
    "Greetings!",
    "Hey, how are you?",
    "Nice to meet you!",
    "Hello, friend!",
    "Hi, hope you’re doing well!",
]
EMOJIS = ["👋", "😊", "🙌", "🌟", "🤗", "😄", "✨", "😎", "😁"]

# Random Greeting generator for when a user uses /hello
def random_greeting():
    message = random.choice(GREETINGS)
    emoji = random.choice(EMOJIS)
    return f"{message} {emoji}"

# Validate date 
def is_valid_future_date(discussion_date_str):
    try:
        parsed_date = datetime.strptime(discussion_date_str, "%m-%d-%Y").date()
        print(parsed_date, date.today())
        return parsed_date > date.today()
    except ValueError:
        return False

def is_valid_time_string(time_str):
    """
    Validates time in HH:MM AM/PM format.
    Returns True if valid, False otherwise.
    """
    pattern = r"^(0[1-9]|1[0-2]):[0-5][0-9] (AM|PM)$"
    return bool(re.match(pattern, time_str))