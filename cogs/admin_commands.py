import random
import discord
from discord.ext import commands
from discord import app_commands


class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="add_achievement", description="Add an achiemevent to the given player [ADMIN]")
    async def add_success(self, interaction: discord.Interaction, user: discord.Member, achievement_name: int) -> None:
        points = await self._search_achievement(achievement_name)

        # - SECURITY -
        if points == -1:
            await interaction.response.send_message("Achievement not found", ephemeral=True, delete_after=5)
            return

        unlocked = await self.bot.db.unlock_achievement(user.id, achievement_name, points)
        # Check if user have the achievement
        if not unlocked:
            await interaction.response.send_message(f"{user.mention} as already unlock this achievement.", ephemeral=True, delete_after=60)
            return

        # Send a message to the log channel
        if self.bot.channel_log:
            await self.bot.channel_log.send(f"{interaction.user} gave the achievement {achievement_name} to {user.mention}")
        if self.bot.main_channel:
            await self.bot.main_channel.send(self._send_random_unlock_message(user, achievement_name))

        # End the command
        await interaction.response.send_message("Done ✅", ephemeral=True)

    @add_success.autocomplete('achievement_name')
    async def achievement_name_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice]:
        achievements = self.bot.achievements_list

        filtered_list = [
            a for a in achievements
            if current.lower() in a['name_en'].lower()
        ]

        return [
            app_commands.Choice(name=f"{achievement['name_en']}", value=achievement['id'])
            for achievement in filtered_list
        ][:25]

    def _send_random_unlock_message(self, user: discord.Member, achievement_name: str) -> str:
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

        return message

    @app_commands.command(name="remove_achievement", description="Remove an achievement from a player [ADMIN]")
    async def remove_success(self, interaction: discord.Interaction, user: discord.Member, achievement_name: int) -> None:
        points = await self._search_achievement(achievement_name)

        # - SECURITY -
        if points == -1:
            await interaction.response.send_message("Achievement not found", ephemeral=True, delete_after=60)
            return
        unlocked = await self.bot.db.remove_achievement(user.id, achievement_name, points)
        # Check if user have the achievement
        if not unlocked:
            await interaction.response.send_message(f"{user.mention} have not this achievement. Can't remove it.", ephemeral=True, delete_after=60)
            return

        # Send a message to the log channel
        if self.bot.channel_log:
            await self.bot.channel_log.send(f"{interaction.user} remove the achievement {achievement_name} to {user.mention}")

        # End the command
        await interaction.response.send_message("Done ✅", ephemeral=True)

    @remove_success.autocomplete('achievement_name')
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
            if a['id'] in unlocked_ids and current.lower() in a['name_en'].lower()
        ]

        # 4. Renvoyer les choix (maximum 25)
        return [
            app_commands.Choice(name=f"{achievement['name_en']}", value=achievement['id'])
            for achievement in filtered_list
        ][:25]

    # :-------------------:
    #    Private methods
    # :-------------------:

    async def _search_achievement(self, achievement_name: int) -> int:
        achievements = self.bot.achievements_list

        points: int = -1
        for value in achievements:
            if achievement_name == value['id']:
                points = value['points']
                break

        return points


async def setup(bot):
    await bot.add_cog(AdminCommands(bot))


# start_event(interaction: discord.Interaction)
# start the event


# stop_event(interaction: discord.Interaction)
# stop the event


# @app_commands.checks.has_role(ROLE_ID)
