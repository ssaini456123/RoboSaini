import random
import time
import asyncpg

import discord
from discord.ext import commands

from utils.buttons import JumpView

STARBOARD_EMOJI = "⭐"
HEADER_TEMPLATE = "**{}** {} in: <#{}>"

class StarboardEntry:
    exists: bool = False
    msg_id: int = 0
    channel_id: int = 0
    stars: int = 0
    bot_msg_id: int = 0
    bot_content_id: int = 0

    def __init__(self, db: asyncpg.Pool, msg_id):
        self.msg_id = msg_id
        self.db = db

    async def fetch(self):
        query = """SELECT * FROM starboard_entries WHERE msg_id=$1"""
        result = await self.db.fetchrow(query, self.msg_id)

        if result is None:
            self.exists = False
            return

        self.exists = True
        self.msg_id = result["msg_id"]
        self.channel_id = result["channel"]
        self.stars = result["stars"]
        self.bot_msg_id = result["bot_message_id"]
        self.bot_content_id = result["bot_content_id"]


class StarboardProperties:
    exists: bool = False

    locked: bool = False
    starboard_id: int = 0
    starboard_threshold: int = 0

    def __init__(self, db: asyncpg.Pool, guild_id: int):
        self.db = db
        self.guild_id = guild_id

    async def fetch(self):
        query = """SELECT * FROM starboard WHERE id=$1"""
        entry = await self.db.fetchrow(query, self.guild_id)

        if entry is None:
            self.exists = False
            return

        self.exists = True
        self.starboard_id = entry["channel"]
        self.threshold = entry["threshold"]
        self.locked = entry["locked"]


class Starboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sb_emoji = ":star:"  # the actual emoji
        self.stars = [":stars:", ":star:", ":dizzy:", ":sparkles:"]
        self.requirement = 2
        self.db: asyncpg.Pool = self.bot.db

    async def is_in_db(self, guild_id):
        query = """
                    SELECT channel, threshold, locked FROM starboard WHERE id=$1
                """
        availability = await self.db.execute(query, guild_id)

        if availability is None:
            return True
        else:
            return False

    async def locked(self, guild_id):
        query = """
                    SELECT locked FROM starboard WHERE id=$1
                """
        locked = await self.db.fetchval(query, guild_id)

        return locked

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def setsb(self, ctx, channel_id: int = None):
        guild_id = ctx.guild.id
        guildChannelIdList = []

        for i in ctx.guild.text_channels:
            cId = i.id
            guildChannelIdList.append(cId)

        if channel_id not in guildChannelIdList:
            # go no further
            await ctx.send(
                "Channel ID does not exist."
            )
            return

        query = """
                    INSERT INTO starboard (id, channel)
                    VALUES($1, $2) 
                    ON CONFLICT(id) DO UPDATE
                    SET channel=$3
                    WHERE starboard.id = $4;
                """
        await self.db.execute(query, ctx.guild.id, channel_id, channel_id, ctx.guild.id)
        await ctx.send("Starboard channel set to: **{}**.".format(channel_id))

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def getsb(self, ctx):
        query = """
                    SELECT channel FROM starboard WHERE id=$1
                """
        channel = await self.db.fetchval(query, ctx.guild.id)

        if channel == None:
            await ctx.send("No starboard found.")
            return

        await ctx.send("The starboard is located at: {}".format(channel))

    @commands.command()
    async def getthreshold(self, ctx):
        query = """
                    SELECT threshold FROM starboard WHERE id=$1
                """

        threshold = await self.db.fetchval(query, ctx.guild.id)

        if threshold is None:
            threshold = 3
        await ctx.send(
            "{} stars required.".format(
                threshold
            )
        )

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def setthreshold(self, ctx, threshold: int = None):
        if threshold is None:
            await ctx.send("Please input a threshold number.")
            return

        query = """
                    INSERT INTO starboard (id, threshold)
                    VALUES ($1, $2) ON CONFLICT(id) DO UPDATE
                    SET threshold=$3 WHERE starboard.id=$4
                """

        await self.db.execute(query, ctx.guild.id, threshold, threshold, ctx.guild.id)

        await ctx.send("Starboard threshold is now: {}.".format(threshold))

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def locksb(self, ctx):
        query = """
                    INSERT INTO starboard (id, locked)
                    VALUES ($1, TRUE) ON CONFLICT(id) DO UPDATE
                    SET locked=TRUE WHERE starboard.id=$2
                """
        
        await self.db.execute(query, ctx.guild.id, ctx.guild.id)
        await ctx.send("Starboard is now locked. Messages starred will be ignored.")

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def unlocksb(self, ctx):
        query = """
                    INSERT INTO starboard (id, locked)
                    VALUES ($1, FALSE) ON CONFLICT(id) DO UPDATE
                    SET locked=FALSE WHERE starboard.id=$2
                """
        await self.db.execute(query, ctx.guild.id, ctx.guild.id)

        await ctx.send(
            "The server starboard is now unlocked. Starred messages will no longer be ignored."
        )

    def get_star(self, stars):
        if stars <= 1:
            return "✨"
        elif stars <= 3:
            return "💫"
        elif stars <= 5:
            return "⭐"
        elif stars <= 7:
            return "🌠"
        else:
            return "🌟"

    def generate_embed_shade(self):
        r = 255
        g = 255
        b = 0

        seed = int(time.time())
        random.seed(seed)

        # now change the shade
        bright_cap = random.randint(0, 220)
        b = bright_cap

        col = discord.Color.from_rgb(r, g, b)
        return col

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        starboard = StarboardProperties(self.db, payload.guild_id)
        await starboard.fetch()

        exists = starboard.exists
        starboard_id = starboard.starboard_id
        locked = starboard.locked

        if not exists:
            return

        if locked:
            # it is, ignore it
            return

        message = await self.bot.get_channel(payload.channel_id).fetch_message(
            payload.message_id
        )

        msg_fmt = ""

        if str(payload.emoji) != STARBOARD_EMOJI:
            # not a starboard reaction - return
            return

        reaction = discord.utils.get(message.reactions, emoji=STARBOARD_EMOJI)

        query = """
                    SELECT threshold FROM starboard WHERE id=$1
                """

        threshold = await self.db.fetchval(query, payload.guild_id)

        if reaction.count < threshold:
            return

        msg_id = payload.message_id

        entry = StarboardEntry(self.db, msg_id)
        await entry.fetch()

        query2 = """
                INSERT INTO starers VALUES (
                    $1,
                    $2
                )"""

        # do we have an embed set?
        if entry.exists:
            bot_msg_id = entry.bot_msg_id

            query = """SELECT * FROM starers WHERE user_id=$1 AND msg_id=$2"""
            starer = await self.db.fetchrow(query, payload.user_id, entry.msg_id)

            if starer is not None:
                return

            query = """UPDATE starboard_entries SET stars = starboard_entries.stars + 1 
                        WHERE msg_id = $1
                    """

            bot_channel = await self.bot.fetch_channel(starboard_id)
            bot_message = await bot_channel.fetch_message(bot_msg_id)

            await self.db.execute(query, entry.msg_id)
            await self.db.execute(query2, payload.user_id, msg_id)

            stars = entry.stars
            stars += 1
            star = self.get_star(stars)

            o_channel = entry.channel_id

            message = HEADER_TEMPLATE.format(star, stars, o_channel)
            await bot_message.edit(content=message)
            return

        channel = self.bot.get_channel(starboard_id)

        embed_color = self.generate_embed_shade()
        sb_embed = discord.Embed(color=embed_color)

        embedVideo = False

        if len(message.attachments) > 0:
            for attachment in message.attachments:
                if (
                    attachment.filename.endswith(".jpg")
                    or attachment.filename.endswith(".jpeg")
                    or attachment.filename.endswith(".png")
                    or attachment.filename.endswith(".webp")
                    or attachment.filename.endswith(".gif")
                ):
                    self.image = attachment.url
                elif (
                    "https://images-ext-1.discordapp.net" in message.content
                    or "https://tenor.com/view/" in message.content
                ):
                    self.image = message.content
                else:
                    embedVideo = True
                    break

                sb_embed.set_image(url=self.image)

        o_msg_url = message.jump_url
        msg_fmt = message.content

        stars = reaction.count
        star = self.get_star(stars)

        bot_message = await channel.send(
            HEADER_TEMPLATE.format(star, stars, payload.channel_id)
        )

        sb_embed.set_author(
            name=message.author.display_name, icon_url=message.author.avatar
        )

        name = " " if not embedVideo else f"File: {str(attachment).rsplit('/')[-1]}"

        buttonLabel = "Jump to video" if embedVideo else "Jump to message"
        jumpView = JumpView(timeout=300, url=o_msg_url, labelName=buttonLabel)

        sb_embed.add_field(name=f"{name}", value=msg_fmt)

        bot_content = await channel.send(embed=sb_embed, view=jumpView)
        query = """INSERT INTO starboard_entries VALUES (
                    $1,
                    $2,
                    $3,
                    $4,
                    $5
                )"""
        await self.db.execute(query, msg_id, bot_message.id, payload.channel_id, reaction.count, bot_content.id)
        await self.db.execute(query2, payload.user_id, msg_id)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        entry = StarboardEntry(self.db, payload.message_id)
        starboard = StarboardProperties(self.db, payload.guild_id)
        await starboard.fetch()
        await entry.fetch()

        starboard_id = starboard.starboard_id
        locked = starboard.locked

        bot_msg_id = entry.bot_msg_id
        content_id = entry.bot_content_id
        if not entry.exists:
            return

        self.bot: commands.Bot

        if not locked:
            channel = await self.bot.fetch_channel(starboard_id)
            bot_msg = await channel.fetch_message(bot_msg_id)
            content_msg = await channel.fetch_message(content_id)

            stars = entry.stars - 1

            if stars <= 0:
                # not possible to have zero stars.
                await bot_msg.delete()
                await content_msg.delete()

                query = """DELETE FROM starboard_entries WHERE msg_id=$1"""
                await self.db.execute(query, payload.message_id)
                return

            star = self.get_star(stars)
            message = HEADER_TEMPLATE.format(star, stars, payload.channel_id)

            query = """DELETE FROM starers WHERE msg_id=$1 AND user_id=$2"""
            query2 = """UPDATE starboard_entries SET stars = $1 WHERE msg_id = $2 """


            await self.db.execute(query, payload.message_id, payload.user_id)
            await self.db.execute(query2, stars, payload.message_id)
            await bot_msg.edit(content=message)
        else:
            # locked - we cant delete stuff in this state.
            return

async def setup(bot):
    await bot.add_cog(Starboard(bot))
