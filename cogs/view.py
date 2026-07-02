import discord
from enum import Enum, auto

class PageView(discord.ui.View):
    def __init__(self, pages: list[discord.Embed]):
        super().__init__(timeout=180)
        self.pages = pages
        self.current_page = 0

        self._update_button_states()

    def _update_button_states(self):
        # Disable PREVIOUS
        if self.current_page == 0:
            self.children[0].disabled = True
        else:
            self.children[0].disabled = False

        if (len(self.pages) - 1) == self.current_page:
            self.children[1].disabled  = True
        else:
            self.children[1].disabled  = False

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.blurple)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page -= 1
        self._update_button_states()
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.blurple)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page += 1
        self._update_button_states()
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)


class FILTER_STATE(Enum):
    ALL = auto()
    UNLOCKED = auto()
    LOCKED = auto()


class AchievementPageView(PageView):
    def __init__(self, bot, achievements: list, target_user, language: str):
        super().__init__(pages=[])

        self.bot = bot
        self.achievements = achievements
        self.target_user = target_user
        self.language = language

        self.filter_state = FILTER_STATE.ALL

    async def _generate_view(self) -> None:
        filter_success = []

        for success in self.achievements:

            if self.filter_state == FILTER_STATE.UNLOCKED:
                if await self.bot.db.check_achievement(self.target_user.id, success['id']):
                    filter_success.append(success)

            elif self.filter_state ==  FILTER_STATE.LOCKED:
                if not await self.bot.db.check_achievement(self.target_user.id, success['id']):
                    filter_success.append(success)

            else:
                filter_success = self.achievements.copy()
                break

        n = 10
        sliced_achievements = [filter_success[i:i + n] for i in range(0, len(filter_success), n)]

        view_list: list[discord.Embed] = []

        for chunck in sliced_achievements:
            description_text: str = "\u200e\n"

            for success in chunck:
                is_curr_unlocked = await self.bot.db.check_achievement(str(self.target_user.id), success['id'])
                if is_curr_unlocked:
                    description_text += f"⦁ **{success['name']}** ⧿ ({success['points']} points) ✅"
                else:
                    description_text += f"⦁ **{success['name']}** ⧿ ({success['points']} points) ❌"

                description_text += f"\n*{success[f'description_{self.language}']}*\n\n"

            embed_obj = discord.Embed(
                title=f"📋 Achievements List of {self.target_user.display_name} 📋",
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

        self.pages = view_list

    @discord.ui.button(label='View unlocked', style=discord.ButtonStyle.secondary, emoji='✅')
    async def unlocked_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.filter_state == FILTER_STATE.UNLOCKED:
            self.filter_state = FILTER_STATE.ALL
            button.label = "View unlocked"
            button.emoji = "✅"
        else:
            self.filter_state = FILTER_STATE.UNLOCKED
            button.label = "Show All"
            button.emoji = "♻️"

            self.children[3].label = "View locked"
            self.children[3].emoji = "❌"

        await self._generate_view()
        self.current_page = 0
        self._update_button_states()
        await interaction.response.edit_message(embed=self.pages[0], view=self)

    @discord.ui.button(label='View locked', style=discord.ButtonStyle.secondary, emoji='❌')
    async def locked_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.filter_state == FILTER_STATE.LOCKED:
            self.filter_state = FILTER_STATE.ALL
            button.label = "View locked"
            button.emoji = "❌"
        else:
            self.filter_state = FILTER_STATE.LOCKED
            button.label = "Show All"
            button.emoji = "♻️"

            self.children[2].label = "View unlocked"
            self.children[2].emoji = "✅"

        await self._generate_view()
        self.current_page = 0
        self._update_button_states()
        await interaction.response.edit_message(embed=self.pages[0], view=self)
