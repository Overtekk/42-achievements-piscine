# THIS MODULE IS INTENDED TO WORKS WITH CUSTOM ACHIEVEMENTS (like saying "BONJOUR!").
# YOU CAN DELETE IT OR USE IT TO ADD YOUR OWNS CUSTOM ACHIEVEMENTS.

import discord
from discord.ext import commands


BONJOUR_MESSAGE: str = "Bonjour!!"


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

        if message.content == BONJOUR_MESSAGE:
            target_success = None

            for success in self.bot.achievements_list:
                if success['name'] == 'Welcome!':
                    target_success = success
                    break
            if not target_success:
                return

            unlocked = await self.bot.db.unlock_achievement(
                message.author.id, target_success['id'], target_success['points']
            )

            if self.achievement_sys and unlocked:
                await self.achievement_sys.send_unlock_success_message(message.author, target_success)

async def setup(bot):
    await bot.add_cog(CustomAchievements(bot))

