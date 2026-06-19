import sys
import os
import discord

from pathlib import Path
from dotenv import load_dotenv
from discord.ext import commands
from utils import print_error, print_log, load_config, load_achievements, check_file_extension
from database.db_manager import DatabaseManager

COGS_FOLDER_PATH = "cogs/"


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
        # Create/Load the database
        bot.db = DatabaseManager()
        # Load the config and achievements list
        bot.config = load_config()
        bot.achievements_list = load_achievements()

        @bot.event
        async def on_ready():
            print_log(f"Bot started as {bot.user.name}")
            # Synchronize slash commands
            guild_object = discord.Object(id=bot.config['server_id'])
            bot.tree.copy_global_to(guild=guild_object)
            await bot.tree.sync(guild=guild_object)

        @bot.event
        async def setup_hook():
            # Create/Load the database
            await bot.db.setup_database()

            # Load cogs
            for file in _clean_file():
                await bot.load_extension(file)


        bot.run(BOT_TOKEN)

        # END
        sys.exit(0)

    except ValueError as e:
        print_error(e)
        sys.exit(1)


def _clean_file() -> list[str]:
    files_list: list[str] = []

    for file in os.listdir(COGS_FOLDER_PATH):
        file_name = Path(file)

        if not check_file_extension(file_name, 'py'):
            continue

        final_filename = "cogs." + f"{file_name.with_suffix('')}"
        files_list.append(final_filename)

    return files_list


if __name__ == "__main__":
    try:
        sys.exit(main())

    except KeyboardInterrupt:
        print_error("\nProgram interrupted by user.")
        sys.exit(130)
