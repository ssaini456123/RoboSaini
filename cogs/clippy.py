import os
import textwrap

import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont

from utils.message import InvalidCommandUsageEmbed


class Clippy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def clippy(self, ctx, *, text: str = None):
        path = "images/clippy.jpg"
        newfile = "images/clippynew.jpg"

        if text == None:
            usage = f"clippy <text...>"
            embed = await InvalidCommandUsageEmbed(
                ctx=ctx, description="{}".format(usage)
            ).send()
            return

        width = 40
        newtext = textwrap.fill(text, width)
        image = Image.open(path)
        font = ImageFont.truetype("images/clippy.ttf", 12)
        draw = ImageDraw.Draw(image)

        draw.text(xy=(12, 12), text=newtext, fill="rgb(0,0,0)", font=font)
        image.save(newfile)
        await ctx.send(file=discord.File(fp=newfile))
        os.remove(newfile)


async def setup(bot):
    await bot.add_cog(Clippy(bot))
