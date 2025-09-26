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

def make_hello_payload():
    example_greetings = [
        f"{random.choice(GREETINGS)} {random.choice(EMOJIS)}",
        f"{random.choice(GREETINGS)} {random.choice(EMOJIS)}",
        f"{random.choice(GREETINGS)} {random.choice(EMOJIS)}",
    ]
    examples = "\n".join(example_greetings)
    return {
        "messages": [
            {
                "role": "user",
                "content": (
                    "You are a Discord bot. Reply with a short, friendly hello message "
                    "that you would send to a user in a Discord server. "
                    "Each time, use a different greeting and a fun emoji that represents hello. "
                    "Here are some examples:\n"
                    f"{examples}\n"
                    "Don't put a '\\n' at the end."
                ),
            }
        ],
        "model": "google/gemma-2-2b-it",
    }

def make_announcement_payload(context, book, section, date_str, time_str):
    if context == "FIRST":
        content = (
            f"You are a Discord bot. Write a relaxed, friendly Discord announcement for our book club. "
            f"Let everyone know we have chosen to read {book} and meeting on {date_str} at {time_str}. The section will be {section}"
            "Encourage those who can't make it to leave comments in the #megathreads channel. "
            "End with a positive message about reading."
        )
    elif context == "FOLLOW_UP":
        content = (
            f"You are a Discord bot. Write a short, friendly follow-up announcement for our book club. "
            f"Remind everyone we're reading {section} next week from {book} and meeting will be on {date_str} at {time_str}. "
            "Encourage those who can't make it to leave comments in the #megathreads channel. "
            "End with a positive message about reading."
        )
    elif context == "FINISH":
        content = (
            f"You are a Discord bot. Write a short, friendly announcement for our book club. "
            f"Let everyone know we just finished reading {book} and like a small congratulations with a congratulatory emoji. "
            "Encourage everyone to contribute to picking a new book."
            "End with a positive message about reading."
        )
    else:
        raise ValueError("Unknown context for announcement payload.")

    return {
        "messages": [
            {
                "role": "user",
                "content": content,
            }
        ],
        "model": "google/gemma-2-2b-it",
    }

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