import discord
from discord.ext import commands
from discord import app_commands
from cogs.view import PageView
from utils import print_log


class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="add_achievement", description="Add an achiemevent to the given player [ADMIN]")
    @app_commands.default_permissions(manage_guild=True)
    async def add_achievement(self, interaction: discord.Interaction, user: discord.Member, achievement_name: int) -> None:
        success = await self._get_achievement_by_id(achievement_name)
        pisciners_role = int(self.bot.config['pisciners_role_id'])
        achievement_sys = self.bot.get_cog("AchievementSystem")

        # - SECURITY -
        if not success:
            await interaction.response.send_message("Achievement not found", ephemeral=True, delete_after=5)
            return
        if not any(role.id == pisciners_role for role in user.roles):
            await interaction.response.send_message(f"{user.mention} is not a pisciners.", ephemeral=True, delete_after=60)
            return

        unlocked = await self.bot.db.unlock_achievement(user.id, achievement_name, success['points'])
        # Check if user have the achievement
        if not unlocked:
            await interaction.response.send_message(f"{user.mention} as already unlocked this achievement.", ephemeral=True, delete_after=60)
            return

        if achievement_sys:
            await achievement_sys.send_unlock_success_message(user, success)

        # Send a message to the log channel
        if self.bot.channel_log:
            await self.bot.channel_log.send(f"{interaction.user.mention} gave the achievement {success['name']} to {user.mention}")
            print_log(f"{interaction.user.mention} gave the achievement {success['name']} to {user.mention}")

        # End the command
        await interaction.response.send_message("Done ✅", ephemeral=True, delete_after=10)

    @add_achievement.autocomplete('achievement_name')
    async def achievement_name_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice]:
        achievements = self.bot.achievements_list

        filtered_list = [
            a for a in achievements
            if current.lower() in a['name'].lower()
        ]

        return [
            app_commands.Choice(name=f"{achievement['name']}", value=achievement['id'])
            for achievement in filtered_list
        ][:25]

    @app_commands.command(name="remove_achievement", description="Remove an achievement from a player [ADMIN]")
    @app_commands.default_permissions(manage_guild=True)
    async def remove_achievement(self, interaction: discord.Interaction, user: discord.Member, achievement_name: int) -> None:
        success = await self._get_achievement_by_id(achievement_name)

        # - SECURITY -
        if not success:
            await interaction.response.send_message("Achievement not found", ephemeral=True, delete_after=60)
            return
        unlocked = await self.bot.db.remove_achievement(user.id, achievement_name, success['points'])
        # Check if user have the achievement
        if not unlocked:
            await interaction.response.send_message(f"{user.mention} have not this achievement. Can't remove it.", ephemeral=True, delete_after=60)
            return

        # Send a message to the log channel
        if self.bot.channel_log:
            await self.bot.channel_log.send(f"{interaction.user.mention} remove the achievement {success['name']} to {user.mention}")
            print_log(f"{interaction.user.mention} remove the achievement {success['name']} to {user.mention}")

        # End the command
        await interaction.response.send_message("Done ✅", ephemeral=True, delete_after=10)

    @remove_achievement.autocomplete('achievement_name')
    async def remove_achievement_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice]:
        target_user = interaction.namespace['user']

        if not target_user:
            return []

        user_id = target_user.id if hasattr(target_user, 'id') else target_user

        if not user_id:
            return []

        unlocked_ids = await self.bot.db.get_user_achievements(str(user_id))
        achievements = self.bot.achievements_list

        filtered_list = [
            a for a in achievements
            if str(a['id']) in unlocked_ids and current.lower() in a['name'].lower()
        ]

        # 4. Renvoyer les choix (maximum 25)
        return [
            app_commands.Choice(name=f"{achievement['name']}", value=achievement['id'])
            for achievement in filtered_list
        ][:25]

    @app_commands.command(name='list_nb_messages', description='See the leaderboard of the numbers of message send by members.')
    @commands.cooldown(1, 20, commands.BucketType.user)
    @app_commands.default_permissions(manage_guild=True)
    async def leaderboard_nb_messages(self, interaction: discord.Interaction) -> None:
        leaderboard = await self.bot.db.get_users_message_count()

        # Slice the list
        n = 20
        sliced_players = [leaderboard[i:i + n] for i in range(0, len(leaderboard), n)]

        view_list: list[discord.Embed] = []
        position = 1

        for chunk in sliced_players:
            description_text: str = "\u200e\n"

            for player_id, points in chunk:
                description_text += f"**{position}**. <@{player_id}> - *messages: {points}*\n"
                position += 1

            embed_obj = discord.Embed(
                title='⌨️ **Number of messages sent** ⌨️',
                description=description_text,
                color=discord.Color.gold()
            )

            view_list.append(embed_obj)

        # If empty
        if not view_list:
            embed_obj = discord.Embed(
                title='⌨️ **Number of messages sent** ⌨️',
                description="\nEmpty :(\n",
                color=discord.Color.gold()
            )

            await interaction.response.send_message(embed=embed_obj, ephemeral=True)
            return

        view_object = PageView(view_list)

        await interaction.response.send_message(embed=view_list[0], view=view_object, ephemeral=True)

    # :-------------------:
    #    Private methods
    # :-------------------:

    async def _get_achievement_by_id(self, achievement_id: int) -> dict | None:
        for a in self.bot.achievements_list:
            if a['id'] == achievement_id:
                return a
        return None


async def setup(bot):
    await bot.add_cog(AdminCommands(bot))
