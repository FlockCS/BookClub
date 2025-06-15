import requests
import yaml
import os
from dotenv import load_dotenv

# Load .env token
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
APPLICATION_ID = os.getenv('DISCORD_APPLICATION_ID')
URL = f"https://discord.com/api/v9/applications/{APPLICATION_ID}/commands"

# read yaml file
with open("discord_commands.yaml", "r") as file:
    yaml_content = file.read()

# turn it into python object
commands = yaml.safe_load(yaml_content)
headers = {"Authorization": f"Bot {TOKEN}", "Content-Type": "application/json"}

# Send the POST request for each command
for command in commands:
    response = requests.post(URL, json=command, headers=headers)
    command_name = command["name"]
    print(f"Command {command_name} created: {response.status_code}")