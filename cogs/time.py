import asyncio
import datetime as datetime
import random
from socket import MsgFlag
import time
import asyncpg

import discord
import pytz
import rapidfuzz

from utils.logger import logErr
from utils.buttons import JumpView
from discord.ext import commands


class Time(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db: asyncpg.Pool = self.bot.db

    async def has_timezone(self, user_id):
        query = """
                SELECT timezone FROM user_settings WHERE
                    id={}
                """.format(
            user_id
        )

        timezoneUser = await self.db.fetchrow(query)

        if timezoneUser == None:
            return False

        return True

    async def get_timezone(self, user_id):
        query = """
            SELECT timezone FROM user_settings WHERE id={}
            """.format(
            user_id
        )

        tz = await self.db.fetchval(query)
        return str(tz)

    def is_timezone_valid(self, tz):
        if tz in pytz.all_timezones:
            return True

        return False

    async def get_similar_timezones(self, tz):
        msg = ""
        ordNum = 1
        similaritiesFound = False
        for timezone in pytz.all_timezones:
            targetSimilarity = rapidfuzz.fuzz.ratio(tz, timezone)

            if targetSimilarity >= 76:
                similaritiesFound = True
                msg += "**{}.** {}\n".format(ordNum, timezone)

                ordNum += 1

        if not similaritiesFound:
            return None

        return msg

    @commands.command()
    async def listtz(self, ctx):
        await ctx.send(
            "Check to see if your timezone is valid using this list:\nhttps://gist.github.com/terrain123456/7c73b88ea17d7cfca51529e48c0b52d7"
        )

    @commands.command()
    async def settz(self, ctx, tz_string: str = None):
        user_id = ctx.author.id

        if tz_string is None:
            usage = f"{ctx.prefix}settz <timezone...>"
            await ctx.send(usage)
            return

        isValid = self.is_timezone_valid(tz_string)

        if isValid is False:
            similarTz = await self.get_similar_timezones(tz_string)
            if similarTz is None:
                # No similarities found period.
                await ctx.send(
                    "The timezone: *{}* is invalid! Run {}listtz for a list of valid timezones.".format(
                        tz_string, ctx.prefix
                    )
                )
                return

            deleteAfter = 10
            embedCol = discord.Color.blurple()

            embed = discord.Embed(color=embedCol)
            embed.add_field(
                name="Did you mean...?",
                value="{}\n*this message will be deleted in {} seconds*".format(
                    similarTz, deleteAfter
                ),
                inline=False,
            )

            timedMsg = await ctx.send(embed=embed)
            await asyncio.sleep(deleteAfter)
            await timedMsg.delete()

            return

        query = """
                    INSERT INTO user_settings (id, timezone) 
                    VALUES({}, '{}')
                    ON CONFLICT(id) DO UPDATE
                    SET timezone='{}'
                    WHERE user_settings.id={}
                """.format(
            user_id, tz_string, tz_string, user_id
        )
        await self.db.execute(query)
        await ctx.send("Timezone successfully set to: *{}*!".format(tz_string))

    @commands.command()
    async def tz(self, ctx):
        user_id = ctx.author.id

        hasTz = await self.has_timezone(user_id)

        if not hasTz:
            await ctx.send(
                "You do not have a timezone set. You can add one by running {}settz".format(
                    ctx.prefix
                )
            )
            return

        tz = await self.get_timezone(user_id)
        await ctx.send("Your timezone is: {}".format(tz))

    @commands.command()
    async def removetz(self, ctx):
        user_id = ctx.author.id
        hasTz = await self.has_timezone(user_id)

        if not hasTz:
            await ctx.send("You do not have a timezone set for me to remove.")
            return

        query = """
                    DELETE FROM user_settings
                    WHERE id={}
                """.format(
            user_id
        )

        await self.db.execute(query)
        await ctx.send("Timezone removed.")

    @commands.command()
    async def time(self, ctx, member: discord.User = None):
        user_id = ctx.message.author.id

        authorHasTz = await self.get_timezone(user_id)

        if member is None:
            # do we have a timezone?
            if authorHasTz is False:
                # nope, go no further!
                await ctx.send(
                    "I couldn't find a timezone of yours in my files, you can add one by running: {}settz <timezone>".format(
                        ctx.prefix
                    )
                )
                return

            authorTz = await self.get_timezone(user_id)

            currentTimezone = pytz.timezone(str(authorTz))
            date = datetime.datetime.now(currentTimezone)

            time_format = f"{date.hour}:{date.minute}"
            twenty_four_hour_clock_conv = datetime.datetime.strptime(
                time_format, "%H:%M"
            )
            conversion = twenty_four_hour_clock_conv.strftime("%I:%M %p")

            viewableTz = authorTz.replace("_", " ")
            await ctx.send(
                f"It is currently: *{conversion}* in {viewableTz}, where you live."
            )
            return
        else:
            member_id = member.id

            userHasTz = await self.has_timezone(member_id)

            if userHasTz is False:
                await ctx.send(
                    "It seems that user doesn't have their timezone in my files. They can add it by running {}settz".format(
                        ctx.prefix
                    )
                )
                return

            userTz = await self.get_timezone(member_id)

            userTimezone = pytz.timezone(userTz)
            date = datetime.datetime.now(userTimezone)

            time_format = f"{date.hour}:{date.minute}"
            twenty_four_hour_clock_conv = datetime.datetime.strptime(
                time_format, "%H:%M"
            )
            conversion = twenty_four_hour_clock_conv.strftime("%I:%M %p")

            await ctx.send(
                f"It is currently: *{conversion}* in {viewableTz}, where *{member.display_name}* lives."
            )
            return


async def setup(bot):
    await bot.add_cog(Time(bot))
