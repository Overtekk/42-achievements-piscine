from enum import Enum

import discord
from discord import app_commands
from discord.ext import commands

from cogs.view import AchievementPageView, PageView
from utils import check_file_extension

PICTURE_EXTENSION = [".png", ".jpg", ".jpeg"]


class Language(str, Enum):
    FR = "fr"
    EN = "en"


class PlayerCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="leaderboard", description="Show the leaderboard")
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def show_leaderboard(self, interaction: discord.Interaction) -> None:
        leaderboard = await self.bot.db.get_leaderboard()

        # Slice the list
        n = 20
        sliced_players = [leaderboard[i : i + n] for i in range(0, len(leaderboard), n)]

        view_list: list[discord.Embed] = []
        position = 1

        for chunk in sliced_players:
            description_text: str = "\u200e\n"

            for player_id, points in chunk:
                description_text += (
                    f"**{position}**. <@{player_id}> - *score: {points}*\n"
                )
                position += 1

            embed_obj = discord.Embed(
                title="🏆 **Leaderboard** 🏆",
                description=description_text,
                color=discord.Color.gold(),
            )

            view_list.append(embed_obj)

        # If empty
        if not view_list:
            embed_obj = discord.Embed(
                title="🏆 **Leaderboard** 🏆",
                description="\nEmpty :(\n",
                color=discord.Color.gold(),
            )

            await interaction.response.send_message(embed=embed_obj, ephemeral=True)
            return

        view_object = PageView(view_list)

        await interaction.response.send_message(
            embed=view_list[0], view=view_object, ephemeral=True
        )

    @app_commands.command(name="achievements", description="Show the achievements list")
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def achievements_list(
        self,
        interaction: discord.Interaction,
        language: Language = Language.EN,
        user: discord.Member = None,
    ) -> None:

        target_user = user or interaction.user

        view_object = AchievementPageView(
            bot=self.bot,
            achievements=self.bot.achievements_list,
            target_user=target_user,
            language=language.value,
        )

        await view_object._generate_view()

        await interaction.response.send_message(
            embed=view_object.pages[0], view=view_object, ephemeral=True
        )

    @app_commands.command(
        name="send_message", description="Send a message to the tutor"
    )
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def send_message_to_tutor(
        self,
        interaction: discord.Interaction,
        message: str,
        picture: discord.Attachment = None,
    ) -> None:
        # PROTECTION
        if len(message) == 0:
            await interaction.response.send_message(
                "ERROR ❌. Can't send empty message.", ephemeral=True, delete_after=10
            )
            return

        # CHECK PICTURE EXTENSION (prevent sending other things than a picture)
        if picture:
            flag = False
            for extension in PICTURE_EXTENSION:
                if check_file_extension(picture.filename, extension):
                    flag = True
                    break

            if not flag:
                await interaction.response.send_message(
                    f"ERROR ❌. Not  picture. Accepted extension: {PICTURE_EXTENSION}",
                    ephemeral=True,
                    delete_after=10,
                )
                return

        embed_obj = discord.Embed(
            title=f"New message from {interaction.user.display_name}",
            description=(f"\u200e\n{message}"),
        )
        embed_obj.set_author(name=f"{interaction.user.display_name}")
        if picture:
            embed_obj.set_image(url=picture.url)

        # Send a message to the log channel
        if self.bot.channel_log:
            await self.bot.channel_log.send(embed=embed_obj)

        # End the command
        await interaction.response.send_message(
            "Done ✅", ephemeral=True, delete_after=10
        )

    @app_commands.command(
        name="information", description="Show global information about the bot"
    )
    @commands.cooldown(1, 360, commands.BucketType.user)
    async def information_command(
        self, interaction: discord.Interaction, language: Language = Language.EN
    ) -> None:
        description_txt = "\u200e\n"

        if language == Language.EN:
            description_txt += (
                "This bot is used to track and award achievements during your piscine! 🏆\n\n"
                "### 🌟 How It Works\n"
                "As you progress through the piscine, complete projects, or interact with the community, "
                "you will unlock various achievements. Each unlocked achievement grants you points and "
                "boosts you on the server leaderboard!\n\n"
                "### 📋 Main Commands\n"
                "• `/achievements` ⧿ View your personal achievement checklist (unlocked ✅ / locked ❌). "
                "You can choose your language for the achievement description. "
                "You can also specify an user to see his achievements list.\n"
                "• `/leaderboard` ⧿ Check the top players of the piscine and see your current standing.\n"
                "• `/information` ⧿ Display this helpful guide with the choosen language.\n\n"
                "### ✉️ Contacting Tutors\n"
                "Some achievements need a proof. To do that, use the **`/send_message`** command! "
                "You can write your demand (please, specify the success name at least), and optionally attach a screenshot/picture if required."
                "Your message will be securely forwarded directly to the tutor team and the success will be granted as soon as possible! "
                "If there is a problem, a tutor will contact you! Don't worry, some achievements can be automatically unlocked.\n"
                "Of course, it's not needed to participate and will not affect your piscine. It's just a fun thing to do while your working! 🫡\n"
                "\nGood luck!"
            )

        else:
            description_txt += (
                "Ce bot est utilisé pour suivre et attribuer des succès pendant votre piscine ! 🏆\n\n"
                "### 🌟 Comment ça fonctionne\n"
                "Au fur et à mesure de votre progression dans la piscine, que ce soit en terminant des projets ou en "
                "interagissant avec la communauté, vous débloquerez divers succès. Chaque succès débloqué vous "
                "accorde des points et vous propulse dans le classement du serveur !\n\n"
                "### 📋 Commandes principales\n"
                "• `/achievements` ⧿ Affiche la liste de vos succès personnels (débloqués ✅ / verrouillés ❌). "
                "Vous pouvez choisir la langue de la description du succès. "
                "Vous pouvez également cibler un utilisateur pour consulter sa liste de succès.\n"
                "• `/leaderboard` ⧿ Consulte le top des joueurs de la piscine et affiche ton rang actuel.\n"
                "• `/information` ⧿ Affiche ce guide d'aide avec le langage choisi.\n\n"
                "### ✉️ Contacter les Tuteurs\n"
                "Certaines réussites nécessitent une preuve. Pour cela, utilisez la commande **`/send_message`** ! "
                "Vous pouvez y écrire votre demande (veuillez spécifier au moins le nom du succès), et facultativement y joindre une capture d'écran/image si nécessaire. "
                "Votre message sera transmis en toute sécurité directement à l'équipe des tuteurs et le succès vous sera accordé dès que possible ! "
                "En cas de problème, un tuteur vous contactera ! Ne vous inquiétez pas, certains succès peuvent se débloquer automatiquement.\n"
                "Bien sûr, il n'est pas obligatoire de participer et cela n'affectera en rien votre piscine. C'est juste un petit jeu amusant pendant que vous travaillez ! 🫡\n"
                "\nBonne chance !"
            )

        embed_obj = discord.Embed(
            title="📒 **Informations** 📒",
            description=description_txt,
            color=discord.Color.dark_green(),
        )

        await interaction.response.send_message(embed=embed_obj, ephemeral=True)


async def setup(bot):
    await bot.add_cog(PlayerCommands(bot))
