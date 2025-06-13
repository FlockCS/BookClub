# bot.py
import os
import logging
import discord
from dotenv import load_dotenv
from discord.ext import commands

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.messages = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)    

@bot.event
async def on_ready():
    print(f"Ready, {bot.user.name}")


bot.run(TOKEN, log_handler=handler, log_level=logging.DEBUG)