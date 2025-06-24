from config import GREETINGS, EMOJIS
import random

# Random Greeting generator for when a user uses /hello
def random_greeting():
    message = random.choice(GREETINGS)
    emoji = random.choice(EMOJIS)
    return f"{message} {emoji}"