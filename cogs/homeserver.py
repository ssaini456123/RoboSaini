import math
from typing import List
import discord
import datetime
import asyncio
from utils.logger import logF
from datetime import datetime
from discord.ext import commands

TESTING = False

if not TESTING:
    VIVA_GUILD = 777342103280680990
    VOTE_CHANNEL = 1083637948219670528
    GENERAL_CHANNEL = 777342103280680992
else:
    # the testing server
    VIVA_GUILD = 678655372197625858
    VOTE_CHANNEL = 986926224926466109
    GENERAL_CHANNEL = 986818795643490376

    logF("Testing mode enabled - Homeserver now points to test server")

VIVA_PFP_DEFAULT = "asset/HS/viva_default.png"
VIVA_HALLOWEEN_ = "asset/HS/viva_halloween.png"
VIVA_CHRISTMAS = ""

TMP_DIR = "local/"
SONG_DUMP_PATH = "{}songs.txt".format(TMP_DIR)

PUBLISH_MONTH = 12
PUBLISH_DAY = 30

class HomeServer(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.day_secs = 60 * 60 * 24  # seconds in a day (secs)
        self.tally_up_day = self.day_secs * 2  # 2 days (secs)
        # after the tally up day (minutes)
        self.archive_day_min = (self.day_secs * 10) / 6
        self.robo_saini_emoji = "🖤"

        self.hearts = ["🤍", "💙", "💚", "🧡"]

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        guild = self.bot.get_guild(payload.guild_id)

        if guild.id != VIVA_GUILD:
            return

        message = await self.bot.get_channel(payload.channel_id).fetch_message(
            payload.message_id
        )

        if str(payload.emoji) in self.hearts:
            await message.add_reaction(self.robo_saini_emoji)

        roles_reactions_list = [
            "<:Valorant:1085737907869982770>",  # Emoji that assigns the "Warframe" role
            "<:Overwatch:1085738389447385169>",  # Emoji that assigns the "Valo" role
            "<:morbius:1021167541277687818>",  # Emoji that assigns the "Apec" role
        ]
        color_roles_reactions_list = [
            "🟨",
            "⬛",
            "🟦",
            "🟥",
            "🟧",
            "🟪",
            "🟩",
            "💗",
            "🟫",
            "⬜",
            "💙",
        ]

        # this is the message id thatll hold all the reactions
        role_reactable_msg_id = 1087939497553051718
        color_reactable_msg_id = 1093248727617130578

        ###################    REACTION ROLES     #############################

        valorantRole = discord.utils.get(payload.member.guild.roles, name="Valo")
        overwatchRole = discord.utils.get(payload.member.guild.roles, name="Overwatch")
        serverRole = discord.utils.get(payload.member.guild.roles, name="Server")

        if payload.message_id == role_reactable_msg_id:
            # the user clicked the warframe emoji
            if str(payload.emoji) == roles_reactions_list[0]:
                await payload.member.add_roles(valorantRole)
            # the user clicked the valorant emoji
            elif str(payload.emoji) == roles_reactions_list[1]:
                await payload.member.add_roles(overwatchRole)
            # the user clicked the apex role
            elif str(payload.emoji) == roles_reactions_list[2]:
                await payload.member.add_roles(serverRole)
            else:
                # DO NOT REMOVE THIS - IF YOU WANT TO ADD A ROLE ADD ANOTHER ELIF STATEMENT
                # THIS IS A FALLBACK BRANCH
                return

        ###################    REACTION Color ROLES     #############################

        yellowRole = discord.utils.get(payload.member.guild.roles, name="Yellow")
        blackRole = discord.utils.get(payload.member.guild.roles, name="Grey")
        cyanRole = discord.utils.get(payload.member.guild.roles, name="Cyan")
        redRole = discord.utils.get(payload.member.guild.roles, name="Red")
        orangeRole = discord.utils.get(payload.member.guild.roles, name="Orange")
        purpleRole = discord.utils.get(payload.member.guild.roles, name="Purple")
        greenRole = discord.utils.get(payload.member.guild.roles, name="Green")
        pinkRole = discord.utils.get(payload.member.guild.roles, name="Pink")
        brownRole = discord.utils.get(payload.member.guild.roles, name="Brown")
        whiteRole = discord.utils.get(payload.member.guild.roles, name="White")
        blueRole = discord.utils.get(payload.member.guild.roles, name="Blue")

        if payload.message_id == color_reactable_msg_id:
            if str(payload.emoji) == color_roles_reactions_list[0]:
                await payload.member.add_roles(yellowRole)
            elif str(payload.emoji) == color_roles_reactions_list[1]:
                await payload.member.add_roles(blackRole)
            elif str(payload.emoji) == color_roles_reactions_list[2]:
                await payload.member.add_roles(cyanRole)
            elif str(payload.emoji) == color_roles_reactions_list[3]:
                await payload.member.add_roles(redRole)
            elif str(payload.emoji) == color_roles_reactions_list[4]:
                await payload.member.add_roles(orangeRole)
            elif str(payload.emoji) == color_roles_reactions_list[5]:
                await payload.member.add_roles(purpleRole)
            elif str(payload.emoji) == color_roles_reactions_list[6]:
                await payload.member.add_roles(greenRole)
            elif str(payload.emoji) == color_roles_reactions_list[7]:
                await payload.member.add_roles(pinkRole)
            elif str(payload.emoji) == color_roles_reactions_list[8]:
                await payload.member.add_roles(brownRole)
            elif str(payload.emoji) == color_roles_reactions_list[9]:
                await payload.member.add_roles(whiteRole)
            elif str(payload.emoji) == color_roles_reactions_list[10]:
                await payload.member.add_roles(blueRole)
            else:
                # DO NOT REMOVE THIS - IF YOU WANT TO ADD A ROLE ADD ANOTHER ELIF STATEMENT
                # THIS IS A FALLBACK BRANCH
                return

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild.id != VIVA_GUILD:
            return

        if message.clean_content.__contains__("charli"):
            await message.add_reaction(self.charli_emoji)
            return

        if message.clean_content.startswith(">") and message.channel.id == VOTE_CHANNEL:
            msg_fmt = message.clean_content.replace(">", "")
            await message.delete()

            robot_msg = await message.channel.send(
                "Event suggestion: **{}**".format(msg_fmt)
            )
            thread = await robot_msg.create_thread(
                name="{}".format(msg_fmt), auto_archive_duration=10080
            )
            to_append_on = await thread.send(
                "Created by: `{}` on: ```{}```".format(
                    message.author.name, datetime.datetime.utcnow()
                )
            )

            await to_append_on.add_reaction("✔️")
            await to_append_on.add_reaction("❌")

            tallyUpTime = 60 * 60 * 24
            autoDeleteTime = 60 * 60 * 24 * 2  # 2 days after the tally up time

            await asyncio.sleep(tallyUpTime)

            for i in thread.members:
                individual_id = i.id
                await thread.send("<@{}>".format(individual_id))

            await thread.send(
                "Hey guys, decision time! Would you like <@593294576026910720> or <@570796674264596490> to make this an event?"
            )
            await thread.send(
                "** This thread will automatically be deleted in 2 days. **"
            )

            await asyncio.sleep(autoDeleteTime)
            await thread.delete()
            await robot_msg.delete()
        else:
            if not message.author.bot and message.channel.id == VOTE_CHANNEL:
                await message.delete()

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild = member.guild
        if guild.id == VIVA_GUILD:
            IDOIR_ROLE = discord.utils.get(member.guild.roles, name="IDOIR")
            await member.add_roles(IDOIR_ROLE)
        else:
            return

    @commands.command()
    async def charlihearts(self, ctx, *, arg: str = None):
        all = False
        if arg == "all":
            all = True
        text = "Counting{} hearts (This may take a while)".format(
            " ALL" if all is True else ""
        )

        await ctx.send(text)

        channel = self.bot.get_channel(GENERAL_CHANNEL)

        hearts = 0
        total_messages = 0

        limit = 99999  # this makes the entire operation very slow.. oh well

        if all:
            guild = self.bot.get_guild(VIVA_GUILD)
            channel: List[discord.TextChannel] = guild.text_channels

            for c in channel:
                async for message in c.history(limit=limit):
                    total_messages += 1
                    for reaction in message.reactions:
                        if reaction.emoji in self.hearts:
                            hearts += 1

            average = total_messages // hearts
            await ctx.reply(
                "Total: {} 🤍's in *all* channels\n**{}** hearts on average!".format(
                    math.floor(hearts), average
                )
            )

            return

        async for message in channel.history(limit=limit):
            total_messages += 1
            for reaction in message.reactions:
                if reaction.emoji in self.hearts:
                    hearts += 1

        average = total_messages // hearts
        await ctx.reply(
            "Total: {} 🤍's\n**{}** hearts on average!".format(
                math.floor(hearts), average
            )
        )





async def setup(bot):
    await bot.add_cog(HomeServer(bot))
