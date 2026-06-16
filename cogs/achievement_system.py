import discord
import json
import sqlite3

from discord.ext import commands

# Get the config
with open('data/config.json', mode='r') as config_file:
    config = json.load(config_file)

CHANNEL = config['channel_id']

# Create the database
database = sqlite3.connect('Database.db')
cursor = database.cursor()

# Create the table if it doesn't exist
cursor.execute(
    """CREATE TABLE IF NOT EXISTS leaderboard
    (discord_name TEXT, achievements count INTEGER)
    """
)
database.commit()

class AchievementSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
