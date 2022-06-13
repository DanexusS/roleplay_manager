import json
import nextcord
from nextcord.ext.commands import MissingRole, CommandNotFound

from constants import LOCALIZATIONS
from typing import Optional


# ФУНКЦИЯ, делающая чистый id пользователя
async def clean_member_id(member_id: str) -> Optional[int]:
    try:
        return int(member_id.replace("<", "").replace(">", "").replace("!", "").replace("@", ""))
    except ValueError:
        return None


async def commit_changes(data, location: str):
    with open(f"json_data\\{location}", "w", encoding="utf8") as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)


async def throw_error(
        interaction: nextcord.Interaction,
        error: Exception
):
    text = error
    if isinstance(error, MissingRole):
        text = LOCALIZATIONS["Errors"]["General"]["Missing-role"][interaction.locale[:2]]
    if isinstance(error, CommandNotFound):
        text = LOCALIZATIONS["Errors"]["General"]["Incorrect-command"][interaction.locale[:2]]

    embed = nextcord.Embed(title=nextcord.Embed.Empty, color=0xED4337)
    embed.set_footer(text=LOCALIZATIONS["Error_Handler"]["Footer"][interaction.locale[:2]])
    embed.add_field(
        name=LOCALIZATIONS["Error_Handler"]["Field_title"][interaction.locale[:2]],
        value=f"```diff\n{text}\n```",
        inline=False
    )

    await interaction.send(embed=embed, ephemeral=True)
