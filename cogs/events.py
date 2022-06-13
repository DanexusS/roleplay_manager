import nextcord

from cogs import user_experience
from general_imports import *

# TODO: добавить новый смайлики и улучшить дизайн старых эмодзи
EMOJIS_ID = {
    "Богатая семья": 955784319702548550,
    "Обычная семья": 955777557826002974,
    "Бедная семья": 955777604357603358,
    "Северяне": 955784315449532456,
    "Южане": 955784858897104916,
    "Техно-гики": 955784858804842506,
    "Валюта": 956604076739682304
}


class EventsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.bot.user} запустился!")

        for title, emoji_id in EMOJIS_ID.items():
            EMOJIS[title] = self.bot.get_emoji(emoji_id)

    # TODO: добавить нормальную систему сохранения "быстрых" данных
    @commands.Cog.listener()
    async def on_close(self):
        print("Closed")

    # TODO: добавить локализацию ника
    @commands.Cog.listener()
    async def on_guild_join(self, guild: nextcord.Guild):
        print(guild.preferred_locale)

    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message):
        user = message.author
        guild = message.guild

        if user.bot or get(guild.roles, name="Игрок") not in user.roles or \
                "/" in message.content or len(message.content) < 50:
            return

        await user_experience.add_xp(guild.id, user.id, 0.5)

    @commands.Cog.listener()
    async def on_member_join(self, member: nextcord.Member):
        user_id = f"{member.id}-{member.guild.id}"
        if not member.bot and not DB_SESSION.query(User).filter(User.id == user_id).first():
            user = User()
            user.id = user_id

            DB_SESSION.add(user)
        DB_SESSION.commit()

    @commands.Cog.listener()
    async def on_member_remove(self, member: nextcord.Member):
        if member.bot:
            return
        User.query.filter(User.id == f"{member.id}-{member.guild.id}").delete()
        DB_SESSION.commit()


def setup(bot: commands.Bot):
    bot.add_cog(EventsCog(bot))
