from discord.ext import commands


class PlayerCommands(commands.Cog):
    pass


# leaderboard(interaction: discord.Interaction)
# to > DatabaseManager.get_leaderboard() and build embedded msg.

# achievements_list(interaction: discord.Interaction, category: str = None, language: str = 'fr')
# read achievements_list.json and show the filtred list


# interaction.response.send_message(embed=..., ephemeral=True)
# @app_commands.choices
