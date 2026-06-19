import discord
from discord import app_commands
from discord.ext import commands


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
            embed_obj.add_field(
                name="EMPTY",
                value="",
                inline=False
            )

        else:
            position = 1
            for player_id, points in leaderboard:
                embed_obj.add_field(
                    name=f"{position}.",
                    value=f"<@{player_id}> | {points}",
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
