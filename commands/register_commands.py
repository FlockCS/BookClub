import requests
import yaml
import os
import sys
import argparse
from dotenv import load_dotenv

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Register Discord commands for Alpha or Prod environment')
    parser.add_argument('environment', choices=['alpha', 'prod'], 
                       help='Environment to register commands for (alpha or prod)')
    
    args = parser.parse_args()
    
    # Load .env token
    load_dotenv()
    
    # Use appropriate token and application ID based on environment
    if args.environment.lower() == 'alpha':
        TOKEN = os.getenv('ALPHA_DISCORD_TOKEN')
        APPLICATION_ID = os.getenv('ALPHA_DISCORD_APPLICATION_ID')
        if not TOKEN:
            print("Error: ALPHA_DISCORD_TOKEN not found in environment variables")
            sys.exit(1)
        if not APPLICATION_ID:
            print("Error: ALPHA_DISCORD_APPLICATION_ID not found in environment variables")
            sys.exit(1)
    else:  # prod
        TOKEN = os.getenv('PROD_DISCORD_TOKEN')
        APPLICATION_ID = os.getenv('PROD_DISCORD_APPLICATION_ID')
        if not TOKEN:
            print("Error: PROD_DISCORD_TOKEN not found in environment variables")
            sys.exit(1)
        if not APPLICATION_ID:
            print("Error: PROD_DISCORD_APPLICATION_ID not found in environment variables")
            sys.exit(1)
    
    URL = f"https://discord.com/api/v9/applications/{APPLICATION_ID}/commands"
    
    print(f"Registering commands for {args.environment.upper()} environment...")
    print(f"Using Application ID: {APPLICATION_ID}")
    
    # read yaml file
    with open("./commands/discord_commands.yaml", "r") as file:
        yaml_content = file.read()
    
    # turn it into python object
    commands = yaml.safe_load(yaml_content)
    headers = {"Authorization": f"Bot {TOKEN}", "Content-Type": "application/json"}
    
    # Send the POST request for each command
    for command in commands:
        response = requests.post(URL, json=command, headers=headers)
        command_name = command["name"]
        print(f"Command {command_name} created: {response.status_code}")

if __name__ == "__main__":
    main()