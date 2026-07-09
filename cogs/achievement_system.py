import random
import discord
from discord.ext import commands, tasks


class AchievementSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # Start the task
        self.send_leaderboard.start()

    def cog_unload(self) -> None:
        self.send_leaderboard.cancel()

    async def send_unlock_success_message(self, user: discord.Member, success) -> None:
        # Create the embeded object
        embed_obj = discord.Embed(
            title="💫 Achivement Unlocked 💫",
            description=(
                "\u200e"
                f"{self._send_random_unlock_message(user, success['name'], success['description_en'])}"
            ),
            color=discord.Color.dark_blue()
        )
        embed_obj.set_thumbnail(url=user.display_avatar.url)

        # Send the message
        if self.bot.main_channel:
            await self.bot.main_channel.send(embed=embed_obj)

    @tasks.loop(hours=4)
    async def send_leaderboard(self) -> None:
        if not self.bot.is_ready():
            return

        leaderboard = await self.bot.db.get_leaderboard()

        # Slice the list
        n = 10
        sliced_players = [leaderboard[i:i + n] for i in range(0, len(leaderboard), n)]

        position = 1
        description_text = "No score yet."

        for chunk in sliced_players:
            description_text: str = "\u200e\n"

            for player_id, points in chunk:
                description_text += f"**{position}**. <@{player_id}> - *score: {points}*\n"
                position += 1

        embed_obj = discord.Embed(
            title='🏆 **Leaderboard - Top 10** 🏆',
            description=description_text,
            color=discord.Color.gold()
        )

        if self.bot.main_channel:
            await self.bot.main_channel.send(embed=embed_obj)

    # :-------------------:
    #    Private methods
    # :-------------------:

    def _send_random_unlock_message(self, user: discord.Member, achievement_name: str, achievement_description: str) -> str:
        n = random.randint(0, 10)

        message = f"{user.mention} have unlocked **{achievement_name}**! 🎉"
        match n:
            case 0:
                message = message
            case 1:
                message = f"{user.mention} have unlocked **{achievement_name}**! GG 🔥"
            case 2:
                message = f"New achievement unlocked for {user.mention}: **{achievement_name}**"
            case 3:
                message = f"**{achievement_name}** have been unlocked by {user.mention}"
            case 4:
                message = f"**{achievement_name}** have been unlocked by {user.mention}. Congrats! 🌟"
            case 5:
                message = f"{user.mention} has made the advancement [**{achievement_name}**]"
            case 6:
                message = f"{user.mention} now possess: **{achievement_name}**. GG 👏"
            case 7:
                message = f"{user.mention} have unlocked the achievement **{achievement_name}**"
            case 8:
                message = f"GG {user.mention} for the achievement: **{achievement_name}**! 🎊"
            case 9:
                message = f"{user.mention} have unlocked **{achievement_name}** 👍"
            case 10:
                message = f"A new achievement have been unlocked by {user.mention}: **{achievement_name}**"

        message += f"\n\n[*{achievement_description}*]"

        return message

async def setup(bot):
    await bot.add_cog(AchievementSystem(bot))

