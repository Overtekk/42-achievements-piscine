import discord
from discord import app_commands
from discord.ext import commands
from utils.config_manager import Difficulty
from cogs.view import PageView
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
        n = 25
        sliced_players = [leaderboard[i:i + n] for i in range(0, len(leaderboard), n)]

        view_list: list[discord.Embed] = []
        position = 1

        for chunk in sliced_players:
            embed_obj = discord.Embed(
                title='🏆 **Leaderboard** 🏆',
                color=discord.Color.gold()
            )

            for player_id, points in chunk:
                embed_obj.add_field(
                    name="",
                    value=f"**{position}**. <@{player_id}>  – *(score: {points})*",
                    inline=False
                )
                position += 1

            view_list.append(embed_obj)

        # If empty
        if not view_list:
            embed_obj = discord.Embed(
                title='🏆 **Leaderboard** 🏆',
                color=discord.Color.gold()
            )

            embed_obj.add_field(name="EMPTY :(", value="", inline=False)
            await interaction.response.send_message(embed=embed_obj, ephemeral=True)
            return

        view_object = PageView(view_list)

        await interaction.response.send_message(embed=view_list[0], view=view_object, ephemeral=True)

    @app_commands.command(name='achievements', description='Show all availables achievements')
    @commands.cooldown(1, 20, commands.BucketType.user)
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
                value="Empty",
                inline=True
            )
            await interaction.response.send_message(embed=embed_obj, ephemeral=True)
            return

        view_object = PageView(view_list)

        await interaction.response.send_message(embed=view_list[0], view=view_object, ephemeral=True)


async def setup(bot):
    await bot.add_cog(PlayerCommands(bot))
