import discord
from discord import app_commands
from discord.ext import commands
from utils.config_manager import Difficulty
from cogs.view import View
from enum import Enum


class Language(str, Enum):
    FR = 'fr'
    EN = 'en'


class PlayerCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='leaderboard', description='Show the leaderboard')
    async def show_leaderboard(self, interaction: discord.Interaction) -> None:
        leaderboard = await self.bot.db.get_leaderboard()

        embed_obj = discord.Embed(
            title='🏆 **Leaderboard** 🏆',
            color=discord.Color.gold()
        )

        if not leaderboard:
            embed_obj.add_field(name="EMPTY", value="", inline=False)

        else:
            position = 1
            for player_id, points in leaderboard:
                embed_obj.add_field(
                    name=f"{position}.",
                    value=f"<@{player_id}> | {points}",
                    inline=False
                )

        await interaction.response.send_message(embed=embed_obj, ephemeral=True)

    @app_commands.command(name='achievements_list', description='Show all availables achievements')
    async def achievements_list(
        self, interaction: discord.Interaction, difficulty: Difficulty = None,
        language: Language = Language.EN
    ) -> None:

        achievements = self.bot.achievements_list

        # Filter by difficulty
        if difficulty:
            filtered_achievements = [a for a in achievements if a['difficulty'] == difficulty]
        else:
            filtered_achievements = achievements

        # Slice the list
        n = 10
        sliced_achievements = [filtered_achievements[i:i + n] for i in range(0, len(filtered_achievements), n)]

        language_str = f"name_{language}"
        description_str = f"description_{language}"
        difficulty_str = ""

        view_list: list[discord.Embed] = []

        for chunck in sliced_achievements:

            embed_obj = discord.Embed(
                title="📋 Achievements list",
                color=discord.Color.og_blurple()
            )
            for success in chunck:
                if success['difficulty'] == Difficulty.EASY:
                    difficulty_str = "⭐"
                elif success['difficulty'] == Difficulty.MEDIUM:
                    difficulty_str = "⭐⭐"
                else:
                    difficulty_str = "⭐⭐⭐"

                embed_obj.add_field(
                    name=f"{difficulty_str} {success[language_str]} ({success['points']} points)",
                    value=f"*{success[description_str]}*",
                    inline=False
                )

            view_list.append(embed_obj)

        # If empty
        if not view_list:
            embed_obj = discord.Embed(
                title="📋 Achievements list",
                color=discord.Color.og_blurple()
            )
            embed_obj.add_field(
                name="",
                value="Empty"
            )
            return

        view_object = View(view_list)

        await interaction.response.send_message(embed=view_list[0], view=view_object, ephemeral=True)


async def setup(bot):
    await bot.add_cog(PlayerCommands(bot))
