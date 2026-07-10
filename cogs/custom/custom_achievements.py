# THIS MODULE IS INTENDED TO WORKS WITH CUSTOM ACHIEVEMENTS (like saying "BONJOUR!").
# YOU CAN DELETE IT OR USE IT TO ADD YOUR OWNS CUSTOM ACHIEVEMENTS.

import discord
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
        await self.bot.db.increment_user_message_count(message.author.id)

        # CHECK NB MESSAGES SEND
        if await self.bot.db.check_user_message_count(message.author.id) == 142:
            await self._unlock_achievement(message.author.id, message.author, 'Spammer')
        elif await self.bot.db.check_user_message_count(message.author.id) == 242:
            await self._unlock_achievement(message.author.id, message.author, 'Spamton')

        # CHECK THE 'BONJOUR!!'
        if message.content == SecretText.BONJOUR_MESSAGE:
            await self._unlock_achievement(message.author.id, message.author, 'Welcome!')

        # CHECK THE SECRET1_1
        if message.content == SecretText.SECRET1_1:
            await self._delete_message(message)

            try:
                await message.author.send(
                    SecretText.FIRST_MESSAGE1
                )
                await message.author.send(
                    SecretText.FIRST_MESSAGE2
                )
                await message.author.send(
                    SecretText.FIRST_MESSAGE3
                )
            except discord.Forbidden:
                print_error(f"{message.author.display_name} can't received DM. Sending ephemeral message.")
                await message.channel.send(
                    f"{message.author.mention} can't send you a DM... 😥", delete_after=10, silent=True
                )

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

async def setup(bot):
    await bot.add_cog(CustomAchievements(bot))

