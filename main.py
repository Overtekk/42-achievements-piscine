import sys
import os
import discord

from dotenv import load_dotenv
from src.utils import print_error, print_log
from discord.ext import commands


def main():
    try:
        # Load the discord token
        if not load_dotenv('.env'):
            raise ValueError("\nCreate the '.env' and put the discord token in it.")
        BOT_TOKEN = os.getenv('DISCORD_TOKEN')
        if BOT_TOKEN is None:
            raise ValueError("\n Missing discord token in the .env file.")

        # Create the bot
        bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

        @bot.event
        async def on_ready():
            print_log(f"Bot started as {bot.user.name}")

        bot.run(BOT_TOKEN)

        # END
        sys.exit(0)

    except ValueError as e:
        print_error(e)
        sys.exit(1)


if __name__ == "__main__":
    try:
        sys.exit(main())

    except KeyboardInterrupt:
        print_error("\nProgram interrupted by user.")
        sys.exit(130)
