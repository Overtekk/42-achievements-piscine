import secrets

import discord
import httpx
from discord import app_commands
from discord.ext import commands, tasks

from utils import print_error, print_log

OAUTH_AUTHORIZE_URL = "https://api.intra.42.fr/oauth/authorize"


class OAuth42(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._http = httpx.AsyncClient(timeout=15.0)

        self._oauth_uid = self.bot.config.get("api_42_uid")
        self._oauth_secret = self.bot.config.get("api_42_secret")
        self._redirect_uri = self.bot.config.get("oauth_redirect_uri", "")
        self._server_url = self.bot.config.get("oauth_server_url", "")

        if self._server_url:
            self.poll_pending.start()
        else:
            print_error(
                "OAuth server URL not configured. Add OAUTH_SERVER_URL to .env. "
                "Link/Unlink commands will not work."
            )

    def cog_unload(self) -> None:
        if self.poll_pending.is_running():
            self.poll_pending.cancel()

    def _generate_oauth_url(self, state: str) -> str:
        return (
            f"{OAUTH_AUTHORIZE_URL}"
            f"?client_id={self._oauth_uid}"
            f"&redirect_uri={self._redirect_uri}"
            f"&response_type=code"
            f"&state={state}"
            f"&scope=public"
        )

    # :-------------------:
    #    Slash commands
    # :-------------------:

    @app_commands.command(
        name="link_42",
        description="Link your 42 account via OAuth to enable achievement tracking",
    )
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def link_42(self, interaction: discord.Interaction) -> None:
        if not self._oauth_uid or not self._redirect_uri or not self._server_url:
            await interaction.response.send_message(
                "OAuth is not configured. Contact an admin.",
                ephemeral=True,
                delete_after=15,
            )
            return

        pisciners_role = int(self.bot.config["pisciners_role_id"])
        if not any(role.id == pisciners_role for role in interaction.user.roles):
            await interaction.response.send_message(
                "Only pisciners can link their 42 account.",
                ephemeral=True,
                delete_after=15,
            )
            return

        state = secrets.token_urlsafe(32)
        discord_user_id = str(interaction.user.id)

        try:
            resp = await self._http.post(
                f"{self._server_url}/42/register",
                json={"state": state, "discord_user_id": discord_user_id},
            )
            if resp.status_code != 201:
                await interaction.response.send_message(
                    "Failed to initiate linking. Try again later.",
                    ephemeral=True,
                    delete_after=15,
                )
                return
        except httpx.HTTPError:
            await interaction.response.send_message(
                "Could not reach the server. Try again later.",
                ephemeral=True,
                delete_after=15,
            )
            return

        oauth_url = self._generate_oauth_url(state)

        embed = discord.Embed(
            title="Link your 42 account",
            description=(
                "Click the button below to authenticate with 42.\n\n"
                "You will be redirected to a confirmation page."
            ),
            color=discord.Color.blue(),
        )

        view = discord.ui.View()
        button = discord.ui.Button(
            label="Authenticate with 42",
            url=oauth_url,
            style=discord.ButtonStyle.link,
        )
        view.add_item(button)

        await interaction.response.send_message(
            embed=embed, view=view, ephemeral=True
        )

    @app_commands.command(
        name="unlink_42",
        description="Unlink your 42 account",
    )
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def unlink_42(self, interaction: discord.Interaction) -> None:
        login = await self.bot.db.get_42_login(str(interaction.user.id))
        if not login:
            await interaction.response.send_message(
                "No 42 account linked.",
                ephemeral=True,
                delete_after=15,
            )
            return

        async with self.bot.db._connect() as db:
            await db.execute(
                "DELETE FROM user_42_links WHERE user_id = ?",
                (str(interaction.user.id),),
            )
            await db.commit()

        await interaction.response.send_message(
            f"Unlinked from 42 account **{login}**.",
            ephemeral=True,
        )

    # :-------------------:
    #    Polling task
    # :-------------------:

    @tasks.loop(seconds=3)
    async def poll_pending(self) -> None:
        if not self.bot.is_ready() or not self._server_url:
            return

        try:
            resp = await self._http.get(f"{self._server_url}/42/pending")
            if resp.status_code != 200:
                return
            pending = resp.json()
        except httpx.HTTPError:
            return

        for entry in pending:
            discord_user_id = entry.get("discord_user_id", "")
            login_42 = entry.get("login_42", "")
            if not discord_user_id or not login_42:
                continue

            await self.bot.db.link_42_account(discord_user_id, login_42)

            guild = self.bot.get_guild(int(self.bot.config["server_id"]))
            if not guild:
                continue
            member = guild.get_member(int(discord_user_id))
            if not member:
                continue

            try:
                await member.send(
                    f"Your 42 account **{login_42}** has been linked! "
                    f"Achievement tracking is now active."
                )
            except discord.Forbidden:
                print_log(
                    f"Could not DM {member.display_name} about successful 42 link."
                )

    @poll_pending.before_loop
    async def before_poll(self) -> None:
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(OAuth42(bot))
