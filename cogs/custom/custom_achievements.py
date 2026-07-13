# THIS MODULE IS INTENDED TO WORKS WITH CUSTOM ACHIEVEMENTS (like saying "BONJOUR!").
# YOU CAN DELETE IT OR USE IT TO ADD YOUR OWNS CUSTOM ACHIEVEMENTS.

import discord
from discord import app_commands
from discord.ext import commands
from utils import print_error
from cogs.custom.message import SecretText


class CustomAchievements(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.achievement_sys = self.bot.get_cog("AchievementSystem")
        self.pisciners_role = int(self.bot.config['pisciners_role_id'])

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        # - SECURITY -
        if message.author.bot or not any(role.id == self.pisciners_role for role in message.author.roles):
            return

        # Increment MESSAGES COUNT
        message_count = await self.bot.db.increment_user_message_count(message.author.id)

        # CHECK NB MESSAGES SEND
        if message_count == 142:
            await self._unlock_achievement(message.author.id, message.author, 'Spammer')
        elif message_count == 242:
            await self._unlock_achievement(message.author.id, message.author, 'Spamton')

        # CHECK THE 'BONJOUR!!'
        if message.content == SecretText.BONJOUR_MESSAGE:
            await self._unlock_achievement(message.author.id, message.author, 'Welcome!')

        # CHECK THE SECRET1_1
        if message.content == SecretText.SECRET1_1:
            await self._delete_message(message)

    @app_commands.command(name='secret', description='Type the secret here')
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def secret_command(self, interaction: discord.Interaction, code: str) -> None:
        if code == SecretText.SECRET1_1:
            if not await self._secret_1(interaction):
                await interaction.response.send_message("can't send you a DM... 😥. Please allow me to send you a DM.", ephemeral=True, delete_after=60)
                return

        await interaction.response.send_message("〰️", ephemeral=True, silent=True, delete_after=0.1)

    # :-------------------:
    #    Private methods
    # :-------------------:

    async def _unlock_achievement(self, user_id: int, user, success_name: str) -> None:
        target_success = None

        for success in self.bot.achievements_list:
            if success['name'] == success_name:
                target_success = success
                break
        if not target_success:
            return

        unlocked = await self.bot.db.unlock_achievement(
            user_id, target_success['id'], target_success['points']
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
            await interaction.user.send(
                SecretText.FIRST_MESSAGE1
            )
            await interaction.user.send(
                SecretText.FIRST_MESSAGE2
            )
            await interaction.user.send(
                SecretText.FIRST_MESSAGE3
            )
        except discord.Forbidden:
            print_error(f"{interaction.user.display_name} can't received DM. Sending ephemeral message.")
            return False
        return True

async def setup(bot):
    await bot.add_cog(CustomAchievements(bot))

