from json import load
import random
from aiohttp import DataQueue
import discord
import datetime
import asyncio
from discord import Colour
from typing import Union, Optional, Any


class InvalidCommandUsageEmbed(discord.Embed):
    """An embed for invalid command usage messages"""

    def __init__(
        self,
        ctx,
        description,
        *,
        colour: Optional[Union[int, Colour]] = None,
        color: Optional[Union[int, Colour]] = None,
        title: Optional[Any] = None,
        url: Optional[Any] = None,
        timestamp: Optional[datetime.datetime] = None,
        additionalInf: bool = False
    ):
        self.ctx = ctx
        self.deleteAfter = 7  # 7 seconds

        heading = ":warning: Invalid command usage!"
        if additionalInf:
            description = description
        else:
            description = "Usage: `{}{}`".format(ctx.prefix, description)

        colour = discord.Colour.dark_red()

        super().__init__(
            colour=colour,
            color=color,
            title=heading,
            type="rich",
            url=url,
            description=description,
            timestamp=timestamp,
        )

    async def send(self):
        msg = await self.ctx.send(embed=self)
        da = self.deleteAfter

        await asyncio.sleep(da)
        await msg.delete()


class QuickEmbed(discord.Embed):
    """A class that supports a faster way of sending embeds."""

    def __init__(
        self,
        ctx,
        description,
        *,
        colour: Optional[Union[int, Colour]] = None,
        color: Optional[Union[int, Colour]] = None,
        title: Optional[Any] = None,
        type="rich",
        url: Optional[Any] = None,
        timestamp: Optional[datetime.datetime] = None
    ):
        colour = discord.Colour.blurple()

        self.ctx = ctx

        super().__init__(
            colour=colour,
            color=color,
            title=title,
            type=type,
            url=url,
            description=description,
            timestamp=timestamp,
        )

    async def send(self):
        await self.ctx.send(embed=self)
