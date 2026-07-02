import discord
from discord import app_commands
from discord.ext import commands
from cogs.view import PageView, AchievementPageView
from enum import Enum


class Language(str, Enum):
    FR = 'fr'
    EN = 'en'


class PlayerCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='leaderboard', description='Show the leaderboard')
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def show_leaderboard(self, interaction: discord.Interaction) -> None:
        leaderboard = await self.bot.db.get_leaderboard()

        # Slice the list
        n = 20
        sliced_players = [leaderboard[i:i + n] for i in range(0, len(leaderboard), n)]

        view_list: list[discord.Embed] = []
        position = 1

        for chunk in sliced_players:
            description_text: str = "\u200e\n"

            for player_id, points in chunk:
                description_text += f"**{position}**. <@{player_id}> - *score: {points}*\n"
                position += 1

            embed_obj = discord.Embed(
                title='🏆 **Leaderboard** 🏆',
                description=description_text,
                color=discord.Color.gold()
            )

            view_list.append(embed_obj)

        # If empty
        if not view_list:
            embed_obj = discord.Embed(
                title='🏆 **Leaderboard** 🏆',
                description="\nEmpty :(\n",
                color=discord.Color.gold()
            )

            await interaction.response.send_message(embed=embed_obj, ephemeral=True)
            return

        view_object = PageView(view_list)

        await interaction.response.send_message(embed=view_list[0], view=view_object, ephemeral=True)

    @app_commands.command(name='achievements', description='Show all availables achievements')
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def achievements_list(
        self, interaction: discord.Interaction, language: Language = Language.EN, user: discord.Member = None
    ) -> None:

        target_user = user or interaction.user

        view_object = AchievementPageView(
            bot=self.bot,
            achievements=self.bot.achievements_list,
            target_user=target_user,
            language=language.value
        )

        await view_object._generate_view()

        await interaction.response.send_message(embed=view_object.pages[0], view=view_object, ephemeral=True)


async def setup(bot):
    await bot.add_cog(PlayerCommands(bot))
