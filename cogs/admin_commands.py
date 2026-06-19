from discord.ext import commands


class AdminCommands(commands.Cog):
    pass


# start_event(interaction: discord.Interaction)
# start the event


# stop_event(interaction: discord.Interaction)
# stop the event

# add_success(interaction: discord.Interaction, user: discord.Member, achievement_id: str)
# valid an achievement, add points, send a message

# remove_success(interaction: discord.Interaction, user: discord.Member, achievement_id: str)

# user: discord.Member
# channel = interaction.client.get_channel(CHANNEL_ID) then await channel.send(embed=...)
# @app_commands.checks.has_role(ROLE_ID)
