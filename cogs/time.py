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
from utils.message import QuickEmbed
from discord.ext import commands


class Time(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db: asyncpg.Pool = self.bot.db

    async def has_timezone(self, user_id):
        query = """
                SELECT timezone FROM user_settings WHERE
                    id=$1
                """

        timezoneUser = await self.db.fetchrow(query, user_id)

        if timezoneUser == None:
            return False

        return True

    async def get_timezone(self, user_id):
        query = """
            SELECT timezone FROM user_settings WHERE id=$1
            """

        tz = await self.db.fetchval(query, user_id)
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
            similarTz = await self.get_similar_timezones(tz_string.strip("_"))
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
                    VALUES($1, $2)
                    ON CONFLICT(id) DO UPDATE
                    SET timezone=$3
                    WHERE user_settings.id=$4
                """
        await self.db.execute(query, user_id, tz_string, tz_string, user_id)
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
                    WHERE id=$1
                """

        await self.db.execute(query, user_id)
        await ctx.send("Timezone removed.")

    def get_hour_meta(self, hour):
        chosen_emoji = ''
        chosen_color_code = ''

        if hour > 19:
            chosen_emoji = '🌙'
            chosen_color_code = '0x000924'
        else:
            chosen_emoji = '☀️'
            chosen_color_code = '0xFFFF00'

        tup = (chosen_emoji, chosen_color_code)
        return tup

    def strip_city_name(self, location: str):
        substr = location.split("/")
        city = substr[1]
        city = city.replace("_", " ")

        return city

    @commands.command()
    async def time(self, ctx, member: discord.User = None):
        user_id = ctx.message.author.id
        authorHasTz = await self.get_timezone(user_id)

        if member is None:
            # do we have a timezone?
            if authorHasTz is False:
                # nope, go no further!
                await ctx.send(
                    "No timezone found.".format(
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

            viewableTz = self.strip_city_name(authorTz)
            meta = self.get_hour_meta(date.hour)

            await ctx.send(f"{meta[0]} It is currently: **{conversion}** in *{viewableTz}*, where you live.")
            return
        else:
            member_id = member.id

            userHasTz = await self.has_timezone(member_id)

            if userHasTz is False:
                await ctx.send(
                    f"{member.name} does not have a timezone set.".format(
                        ctx.prefix
                    )
                )
                return

            userTz = await self.get_timezone(member_id)

            userTimezone = pytz.timezone(userTz)
            date = datetime.datetime.now(userTimezone)

            time_format = f"{date.hour}:{date.minute}"
            
            meta = self.get_hour_meta(date.hour)
            viewableTz = self.strip_city_name(userTz)

            twenty_four_hour_clock_conv = datetime.datetime.strptime(
                time_format, "%H:%M"
            )

            conversion = twenty_four_hour_clock_conv.strftime("%I:%M %p")

            await ctx.send(f"{meta[0]} It is currently: **{conversion}** in *{viewableTz}*, where {member.name} lives.")


async def setup(bot):
    await bot.add_cog(Time(bot))