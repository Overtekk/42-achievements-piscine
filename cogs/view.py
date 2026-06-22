import discord

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
