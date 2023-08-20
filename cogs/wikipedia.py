import textwrap

import discord
from pytz import NonExistentTimeError
import wikipedia
from utils.message import InvalidCommandUsageEmbed, QuickEmbed
from discord.ext import commands


class Wikipedia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def wikipedia(self, ctx, *, query: str = None):
        if query == None:
            await InvalidCommandUsageEmbed(
                ctx=ctx, description="wikipedia <query>..."
            ).send()
            return

        search = ""

        try:
            search = wikipedia.summary(query)
        except:
            await ctx.send(
                "`{}` isn't very specific. Try adding more detail to your search.".format(
                    query
                )
            )

        shorten = textwrap.wrap(search, 700, break_long_words=True)

        await QuickEmbed(
            ctx=ctx,
            title="Wikipedia",
            description=shorten[0] + "...",
        ).send()


async def setup(bot):
    await bot.add_cog(Wikipedia(bot))
