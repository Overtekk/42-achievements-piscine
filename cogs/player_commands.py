import discord
from discord import app_commands
from discord.ext import commands
from utils.config_manager import Difficulty
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

        filtered_achievements = achievements
        if difficulty:
            pass

        embed_obj = discord.Embed(
            title="📋 Achievements list",
            color=discord.Color.og_blurple()
        )

        language_str = f"name_{language}"
        description_str = f"description_{language}"
        difficulty_str = ""

        if difficulty == Difficulty.MEDIUM:
            difficulty_str = "⭐⭐"
        elif difficulty == Difficulty.HARD:
            difficulty_str = "⭐⭐⭐"
        else:
            difficulty_str = "⭐"

        for success in filtered_achievements:
            embed_obj.add_field(
                name=f"{difficulty_str} {success[language_str]} ({success['points']} points)",
                value=f"*{success[description_str]}*",
                inline=False
            )

        await interaction.response.send_message(embed=embed_obj, ephemeral=True)


async def setup(bot):
    await bot.add_cog(PlayerCommands(bot))


# leaderboard(interaction: discord.Interaction)
# to > DatabaseManager.get_leaderboard() and build embedded msg.

# achievements_list(interaction: discord.Interaction, category: str = None, language: str = 'fr')
# read achievements_list.json and show the filtred list


# interaction.response.send_message(embed=..., ephemeral=True)
# @app_commands.choices
