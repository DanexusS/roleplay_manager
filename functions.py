import json
import nextcord


# ФУНКЦИЯ, делающая чистый id пользователя
async def clean_member_id(member_id):
    try:
        return int(str(member_id).replace("<", "").replace(">", "").replace("!", "").replace("@", ""))
    except ValueError:
        return ""


async def commit_changes(data, location):
    json_file = open(f"json_data\\{location}", "w", encoding="utf8")
    json.dump(data, json_file, ensure_ascii=False, indent=4)


async def throw_error(interaction, error):
    text = error

    # if isinstance(error, MissingRole):
    #     text = f"- У вас нет роли \"Игрок\" для использования этой команды."
    # if isinstance(error, MissingPermissions):
    #     text = "- У вас недостаточно прав для использования этой команды. (Как иронично)"
    # if isinstance(error, CommandNotFound):
    #     text = "- Неверная команда! Для получения списка команд достаточно нажать \"/\""

    embed = nextcord.Embed(title="⮮ __**БОТ СТОЛКНУЛСЯ С ОШИБКОЙ:**__", color=0xed4337)
    embed.add_field(name="**Причина:**",
                    value=f"```diff\n{text}\n```",
                    inline=False)
    await interaction.send(embed=embed, delete_after=180)
