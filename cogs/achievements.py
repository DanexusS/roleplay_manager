from general_imports import *

# TODO: добавить систему достижений с наградами
# TODO: добавить нужные команды для показа ачивок
# TODO: добавить в профиль процентное прохождение достижений
# TODO: добавить локализацию выводов для англ и рус языков
# TODO: оптимизировать код


class AchievementsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @nextcord.slash_command(
        description="Look through all the available achievements and their rewards.",
        description_localizations={
            Locale.ru: "Просмотреть всевозможные достижения и их наград."
        },
        guild_ids=TEST_GUILDS_ID
    )
    async def achievements_showcase(self, interaction: Interaction):
        pass


def setup(bot: commands.Bot):
    bot.add_cog(AchievementsCog(bot))
