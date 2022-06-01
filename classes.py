import nextcord
from typing import Optional


class Paginator(nextcord.ui.View):
    def __init__(
            self,
            pages: list,
            extra_item: Optional[nextcord.ui.Item] = None
    ):
        super().__init__()

        self.current_page = 0
        self.pages = pages

        if extra_item:
            self.add_item(extra_item)

        if len(pages) != 1:
            self.add_item(PageButton(self, "⬅️", -1))
            self.add_item(PageNumberButton(self))
            self.add_item(PageButton(self, "➡️", 1))

    async def update_message(self, message: nextcord.Message):
        await message.edit(
            view=None
        )
        await message.edit(
            embed=self.pages[self.current_page],
            view=self
        )


class PageNumberButton(nextcord.ui.Button):
    def __init__(self, parent: Paginator):
        super().__init__(label=f"Страница {parent.current_page + 1}")

        self.parent = parent
        self.disabled = True

    async def update(self):
        self.label = f"Страница {self.parent.current_page + 1}"


class PageButton(nextcord.ui.Button):
    def __init__(self, parent: Paginator, emoji: str, direction: int):
        super().__init__(emoji=emoji)

        self.parent = parent
        self.direction = direction

    async def callback(self, interaction: nextcord.Interaction):
        if 0 <= self.parent.current_page + self.direction < len(self.parent.pages):
            self.parent.current_page += self.direction

            for child in self.parent.children:
                if not isinstance(child, PageButton):
                    await child.update()

            await self.parent.update_message(interaction.message)
