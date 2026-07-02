import discord
from discord import app_commands
from discord.ext import commands
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

        achievements = self.bot.achievements_list
        target_user = user or interaction.user

        # Slice the list
        n = 10
        sliced_achievements = [achievements[i:i + n] for i in range(0, len(achievements), n)]

        view_list: list[discord.Embed] = []

        for chunck in sliced_achievements:
            description_text: str = "\u200e\n"

            for success in chunck:
                if await self.bot.db.check_achievement(target_user.id, success['id']):
                    description_text += f"⦁ **{success['name']}** ⧿ ({success['points']} points) ✅"
                else:
                    description_text += f"⦁ **{success['name']}** ⧿ ({success['points']} points) ❌"

                description_text += f"\n*{success[f'description_{language}']}*\n\n"

            if user:
                embed_obj = discord.Embed(
                    title=f"📋 Achievements List of {target_user.display_name} 📋",
                    description=description_text,
                    color=discord.Color.og_blurple()
                )
            else:
                embed_obj = discord.Embed(
                    title="📋 Personal Achievements List 📋",
                    description=description_text,
                    color=discord.Color.og_blurple()
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
