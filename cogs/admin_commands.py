import random
import discord
from discord.ext import commands
from discord import app_commands
from utils import print_log


class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="add_achievement", description="Add an achiemevent to the given player [ADMIN]")
    @app_commands.default_permissions(manage_guild=True)
    async def add_achievement(self, interaction: discord.Interaction, user: discord.Member, achievement_name: int) -> None:
        success = await self._get_achievement_by_id(achievement_name)

        # - SECURITY -
        if not success:
            await interaction.response.send_message("Achievement not found", ephemeral=True, delete_after=5)
            return

        unlocked = await self.bot.db.unlock_achievement(user.id, achievement_name, success['points'])
        # Check if user have the achievement
        if not unlocked:
            await interaction.response.send_message(f"{user.mention} as already unlocked this achievement.", ephemeral=True, delete_after=60)
            return

        # Send a message to the log channel
        if self.bot.channel_log:
            await self.bot.channel_log.send(f"{interaction.user.mention} gave the achievement {success['name']} to {user.mention}")
            print_log(f"{interaction.user.mention} gave the achievement {success['name']} to {user.mention}")
        if self.bot.main_channel:
            await self.bot.main_channel.send(self._send_random_unlock_message(user, success['name'], success['description_en']))

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

        message += f"\n[*{achievement_description}*]"

        return message

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


# start_event(interaction: discord.Interaction)
# start the event


# stop_event(interaction: discord.Interaction)
# stop the event


# @app_commands.checks.has_role(ROLE_ID)
