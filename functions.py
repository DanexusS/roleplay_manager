import json
from typing import Optional
import nextcord


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

    # if isinstance(error, MissingRole):
    #     text = f"- У вас нет роли \"Игрок\" для использования этой команды."
    # if isinstance(error, MissingPermissions):
    #     text = "- У вас недостаточно прав для использования этой команды. (Как иронично)"
    # if isinstance(error, CommandNotFound):
    #     text = "- Неверная команда! Для получения списка команд достаточно нажать \"/\""

    embed = nextcord.Embed(title=nextcord.Embed.Empty, color=0xed4337)
    embed.add_field(
        name="**Причина:**",
        value=f"```diff\n{text}\n```",
        inline=False
    )

    await interaction.send(
        embed=embed,
        ephemeral=True
    )
