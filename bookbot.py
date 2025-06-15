import os
import logging
import discord
from dotenv import load_dotenv
from discord.ext import commands

# Load .env token
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Configure logging
logging.basicConfig(
    filename='discord.log',
    level=logging.DEBUG,
    format='%(asctime)s:%(levelname)s:%(name)s: %(message)s'
)

# Set intents
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.members = True

# Create bot
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Ready, {bot.user.name}")

@bot.command(name='hello')
async def hello_world(ctx):
    response = "Hi Flock, this is the book bot to track books."
    await ctx.send(response)

# Run bot (without log_handler/log_level)
bot.run(TOKEN)
