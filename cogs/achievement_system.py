import discord
from discord.ext import commands


class AchievementSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


async def setup(bot):
    await bot.add_cog(AchievementSystem(bot))

