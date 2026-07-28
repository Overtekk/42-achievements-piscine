import os
import sys
from pathlib import Path

import discord
from discord.ext import commands
from dotenv import load_dotenv

from database.db_manager import DatabaseManager
from utils import load_achievements, load_config, print_error, print_log

COGS_FOLDER_PATH = "cogs/"
base_path = Path(COGS_FOLDER_PATH).parent


def main():
    try:
        # Load the discord token
        print_log("Finding the '.env'...")
        if not load_dotenv(".env"):
            raise ValueError("\nCreate the '.env' and put the discord token in it.")
        BOT_TOKEN = os.getenv("DISCORD_TOKEN")
        if BOT_TOKEN is None:
            raise ValueError("\n Missing discord token in the .env file.")
        print_log("Bot Token found!")

        # Create the bot
        print_log("Loading Discord components...")
        bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())
        bot.channel_log = None
        bot.main_channel = None
        # Create/Load the database
        bot.db = DatabaseManager()
        # Load the config and achievements list
        print_log("Loading the configuration...")
        bot.config = load_config()
        print_log("Loading the achievements list...")
        bot.achievements_list = load_achievements()

        @bot.event
        async def on_ready():
            print_log(f"Bot started as {bot.user.name}")

            # Synchronize slash commands
            guild_object = discord.Object(id=bot.config["server_id"])
            bot.tree.copy_global_to(guild=guild_object)
            await bot.tree.sync(guild=guild_object)

            # - Usefull -
            bot.channel_log = await bot.fetch_channel(bot.config["channel_log_id"])
            bot.main_channel = await bot.fetch_channel(bot.config["channel_id"])

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
    skipped_files = ["view.py", "message.py"]
    print_log(f"Loading cogs...\nSkipping: {skipped_files}")

    for file_path in Path(COGS_FOLDER_PATH).rglob("*.py"):
        if file_path.name in skipped_files:
            continue

        relative_path = file_path.relative_to(base_path)
        clean_path = relative_path.with_suffix("")
        final_filename = ".".join(clean_path.parts)

        files_list.append(final_filename)

    print_log(f"Found {len(files_list)} cogs to load.\n{files_list}")
    return files_list


if __name__ == "__main__":
    try:
        sys.exit(main())

    except KeyboardInterrupt:
        print_error("\nProgram interrupted by user.")
        sys.exit(130)
