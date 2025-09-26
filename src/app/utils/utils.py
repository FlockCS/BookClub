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

def make_announcement_payload(context, book, section, dt, time_str):
    weekday = dt.strftime('%A')
    month = dt.strftime('%B')
    day = get_ordinal(dt.day)
    year = dt.year
    formatted_date = f"{weekday}, {month} {day} {year}"
    if context == "FIRST":
        content = (
            f"You are a Discord bot. Write a simple, friendly announcement for our book club. "
            f"Let everyone know we have chosen to read {book} and will meet on {formatted_date} at {time_str}. "
            f"The section will be {section}. "
            "If you can't make it, leave your thoughts in the #megathreads channel. "
            "Use 2 or 3 emojis related to books or reading, spaced throughout the message. "
            "Keep the message concise and not overly enthusiastic."
        )
    elif context == "FOLLOW_UP":
        content = (
            f"You are a Discord bot. Write a short, friendly reminder for our book club. "
            f"We're reading {section} from {book} and meeting on {formatted_date} at {time_str}. "
            "If you can't make it, leave your thoughts in the #megathreads channel. "
            "Use 2 or 3 emojis related to books or reading, spaced throughout the message. "
            "Keep the message concise and not overly enthusiastic."
        )
    elif context == "FINISH":
        content = (
            f"You are a Discord bot. Write a short, friendly announcement for our book club. "
            f"Let everyone know we just finished reading {book}. "
            "Congratulate the group simply and encourage everyone to help pick the next book. "
            "Use 2 or 3 emojis related to books or reading, spaced throughout the message. "
            "Keep the message concise and not overly enthusiastic."
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

def get_ordinal(n):
    if 10 <= n % 100 <= 20:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
    return str(n) + suffix

