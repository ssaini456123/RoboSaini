import asyncio
import json
import os
import random
import time
from typing import Optional, Union
import urllib.parse
import uuid

import aiohttp
import aiofiles
import discord
from discord.emoji import Emoji

from discord.enums import ButtonStyle
from discord.partial_emoji import PartialEmoji
from utils.logger import logF
from discord.ext import commands

from utils.message import InvalidCommandUsageEmbed

MAX_IMAGES_DOWNLOAD = 9
INTERACTION_TIMEOUT = 5

TESTING = False

if TESTING:
    logF("Ai.py is in testing mode.")


class RegenerateButton(discord.ui.Button):
    buttonColor = ButtonStyle.green

    def __init__(self, ctx, oldPrompt, generateFn):
        super().__init__(style=self.buttonColor, label="Regenerate", emoji="🔄", row=2)

        self.generateFn = generateFn
        self.oldPrompt = oldPrompt

        self.ctx = ctx

    async def callback(self, interaction: discord.Interaction):
        ctx = self.ctx
        oldPrompt = self.oldPrompt

        await interaction.response.send_message(
            "Alright, I will generate another image of: *{}* for you. Hang tight!".format(
                oldPrompt
            ),
            ephemeral=True,
        )

        img = await self.generateFn(self.oldPrompt)
        await ctx.reply(
            "I have generated another image of: *{}*".format(
                oldPrompt, ctx.author.display_name
            )
        )

        # latch whats basically the old button back on, allowing to re-generate more images
        # bugs may occur, this has not been tested thoroughly
        regenView = AiView(
            ctx=ctx,
            timeout=INTERACTION_TIMEOUT,
            oldPrompt=oldPrompt,
            generateFn=self.generateFn,
        )
        await self.ctx.send(file=discord.File(fp=img), view=regenView)

        # general cleanup here...
        os.remove(img)


class AiView(discord.ui.View):
    def __init__(self, *, ctx, timeout, oldPrompt, generateFn):
        super().__init__(timeout=timeout)
        self.add_item(
            RegenerateButton(ctx=ctx, oldPrompt=oldPrompt, generateFn=generateFn)
        )


class AI(commands.Cog):
    # TODO: Remove most of the COLAB specific stuff that R. Saini used to have for her own AI.
    # Use craiyon for everything now

    def __init__(self, bot):
        self.bot = bot

        # HTTP stuff for Crayon
        # Achieved through RE'ing the backend.
        self.crayon_url = "https://backend.craiyon.com/generate"
        self.headers = {}
        self.headers["Content-Type"] = "application/json"

        self.save_path = "asset/ai"

    async def download_image(self, prompt: str = None):
        # build our request
        IR = {"prompt": prompt}

        await asyncio.sleep(1)

        data = json.dumps(IR)

        to_json = None
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.crayon_url, data=data, headers=self.headers
            ) as resp:
                to_json = await resp.json()

        random.seed(time.time())

        path = ""

        # the template to strip out
        data_url_template = "data:image/jpeg;base64,"

        img_id = uuid.uuid4()

        randIndex = random.randint(0, 8)

        if TESTING:
            logF(
                "\nRandom index chosen from seeded random number generator: {} \n".format(
                    randIndex
                )
            )

        url_fmt = "{}{}".format(data_url_template, to_json["images"][randIndex])

        # use urlopen to open our data URI
        # and write its contents to an image.jpg file
        response = urllib.request.urlopen(url_fmt)
        save_direct = "{}/{}_.png".format(self.save_path, img_id)

        path = save_direct

        async with aiofiles.open(save_direct, mode="wb") as f:
            await f.write(response.file.read())

        return path

    @commands.command()
    async def imagine(self, ctx: commands.Context, *, prompt: str = None):
        if prompt is None:
            await InvalidCommandUsageEmbed(
                ctx=ctx, description="imagine <prompt>"
            ).send()
            return

        old_msg_url = ctx.message.jump_url
        author_name = ctx.author.display_name

        await ctx.send(
            "Please wait while i generate an image of: **{}**!\t".format(prompt)
        )

        downloadedImage = await self.download_image(prompt)

        replyMsg = ""

        # make the reply more human like
        replyMsg += "Hey *{}*! Your image has been generated!\n".format(author_name)

        regenView = AiView(
            ctx=ctx,
            timeout=INTERACTION_TIMEOUT,
            oldPrompt=prompt,
            generateFn=self.download_image,
        )

        await ctx.reply(file=discord.File(fp=downloadedImage), view=regenView)

        # general cleanup here...
        os.remove(downloadedImage)


async def setup(bot):
    await bot.add_cog(AI(bot))
