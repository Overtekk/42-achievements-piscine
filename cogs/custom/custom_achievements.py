# THIS MODULE IS INTENDED TO WORKS WITH CUSTOM ACHIEVEMENTS (like saying "BONJOUR!").
# YOU CAN DELETE IT OR USE IT TO ADD YOUR OWNS CUSTOM ACHIEVEMENTS.

import re

import discord
from discord import app_commands
from discord.ext import commands

from cogs.custom.message import SecretText
from utils import print_error, print_log

ROLE_NAME = "secret"


class CustomAchievements(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.achievement_sys = self.bot.get_cog("AchievementSystem")
        self.pisciners_role = int(self.bot.config["pisciners_role_id"])

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        # - SECURITY -
        if (
            message.author.bot
            or not message.guild
            or not isinstance(message.author, discord.Member)
            or not any(role.id == self.pisciners_role for role in message.author.roles)
        ):
            return

        # Increment MESSAGES COUNT
        message_count = await self.bot.db.increment_user_message_count(
            message.author.id
        )

        # CHECK NB MESSAGES SEND
        if message_count == 42:
            await self._unlock_achievement(message.author.id, message.author, "Spammer")
        elif message_count == 142:
            await self._unlock_achievement(message.author.id, message.author, "Spamton")

        # CHECK THE 'BONJOUR!!'
        if message.content == SecretText.BONJOUR_MESSAGE:
            await self._unlock_achievement(
                message.author.id, message.author, "Welcome!"
            )

        # DELETE SECRET MESSAGE
        if re.search(r"FYAEITOTOHISPPIT", message.content, re.IGNORECASE) or re.search(r"\?best", message.content, re.IGNORECASE):
            print_log(
                f"Deleted message from {message.author.display_name} ({message.content})"
            )
            await self._delete_message(message)
            return

    @app_commands.command(name="secret", description="Type the secret here")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def secret_command(self, interaction: discord.Interaction, code: str) -> None:
        print_log(
            f"{interaction.user.display_name} use the secret message with the code '{code}'"
        )

        if code == SecretText.SECRET1_1:
            if not await self._secret_1(interaction):
                await interaction.response.send_message(
                    "can't send you a DM... 😥. Please allow me to send you a DM.",
                    ephemeral=True,
                    delete_after=60,
                )
            else:
                await interaction.response.send_message(
                    "Check your DMs! 📩", ephemeral=True
                )
            return

        if code == SecretText.SECRET2_1:
            await interaction.response.send_message(
                "Find a word with it! Use this command again with `/secret secret_message=YOURCODE` followed by the code. Try using it right now. Maybe you will be helped?",
                ephemeral=True,
            )
            return

        if code == SecretText.SECRET_3_1:
            await self._secret_4_role(interaction)
            await interaction.response.send_message(
                "Something has appeared...", ephemeral=True
            )
            return

        if code == SecretText.SECRET_4:
            await self._unlock_achievement(
                interaction.user.id, interaction.user, "Secret #1"
            )
            await interaction.response.send_message(
                "Secret unlocked!", ephemeral=True
            )
            return

        elif code.startswith(SecretText.SECRET_3_2):
            message = await self._secret_3_hint(code)
            await interaction.response.send_message(message, ephemeral=True)
            return

        if not code.startswith(SecretText.SECRET_3_2):  # noqa: SIM102
            if re.search(r"(?:PHOTOSTAT|PHOTO|FYAEITOTOHISPPIT)", code, re.IGNORECASE):
                await interaction.response.send_message(
                "⚠️ Don't forget to format your code using `secret_message=YOURCODE` (e.g. `/secret code:secret_message=...`)!",
                ephemeral=True,
            )
                return

        # FALLBACK
        await interaction.response.send_message(
            "Not a valid code.", ephemeral=True, silent=True, delete_after=30
        )

    # :-------------------:
    #    Private methods
    # :-------------------:

    async def _unlock_achievement(self, user_id: int, user, success_name: str) -> None:
        target_success = None

        for success in self.bot.achievements_list:
            if success["name"] == success_name:
                target_success = success
                break
        if not target_success:
            return

        unlocked = await self.bot.db.unlock_achievement(
            user_id, target_success["id"], target_success["points"]
        )

        if self.achievement_sys and unlocked:
            await self.achievement_sys.send_unlock_success_message(user, target_success)

    async def _delete_message(self, message: discord.Message) -> None:
        try:
            await message.delete()
        except discord.Forbidden:
            print_error("Missing permission to delete message.")
        except discord.NotFound:
            pass

    async def _secret_1(self, interaction: discord.Interaction) -> bool:
        try:
            await interaction.user.send(SecretText.FIRST_MESSAGE1)
            await interaction.user.send(SecretText.FIRST_MESSAGE2)
            await interaction.user.send(SecretText.FIRST_MESSAGE3)

        except discord.Forbidden:
            print_error(
                f"{interaction.user.display_name} can't received DM. Sending ephemeral message."
            )
            return False
        return True

    async def _secret_3_hint(self, raw_code: str) -> str:
        code = raw_code.removeprefix("secret_message=")

        CODE = "PHOTOSTAT"

        if not code:
            return "Please. Put a code."
        if len(code) > 16:
            return "Code too long."
        if len(code) <= 4:
            return "Need minimum 4 letters."

        good: int = 0
        for guess_letter, secret_letter in zip(code.upper(), CODE):
            if guess_letter == secret_letter:
                good += 1

        if good in (0, 1):
            return f"{good} letter are in the right place."
        return f"{good} letters are in the right place."

    async def _secret_4_role(self, interaction: discord.Interaction) -> None:
        guild = interaction.guild
        member = interaction.user

        role = discord.utils.get(guild.roles, name=ROLE_NAME)

        if role not in member.roles:
            try:
                await member.add_roles(role, reason="Found Success #1")
            except discord.Forbidden:
                print_error("Bot doesn't have permission to manage members roles.")
            except discord.HTTPException:
                print_error("HTTP error when attempting to give role to a member.")


async def setup(bot):
    await bot.add_cog(CustomAchievements(bot))
