from general_imports import *


class AchievementsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot


def setup(bot: commands.Bot):
    bot.add_cog(AchievementsCog(bot))
