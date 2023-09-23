import asyncio
import json
import os
import discord
from discord.ext import commands

MASSNICK_SAVE_LOC = "asset/disk/"

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        #self.db = self.bot.db

    def convert_to_seconds(self, s):
        seconds_per_unit = {
            "s": 1,
            "m": 60,
            "h": 3600,
            "hr": 3600,
            "d": 86400,
            "w": 604800,
            "y": 31536000,
            "yr": 31536000,
        }
        return int(s[:-1]) * seconds_per_unit[s[-1]]

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason: str = None):
        await ctx.send("Banned member: {} for: {}".format(member.display_name, reason))
        await member.ban(reason=reason)
    
    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def massnick(self, ctx: commands.Context, *,  name: str = None):
        msg = await ctx.send("Saving all usernames...")

        oldNames = {}

        guild = ctx.guild
        count = 0
        for members in guild.members:
            count += 1
            oldNames[str(members.id)] = members.display_name
            # now edit the username
            try:
                await members.edit(nick=name)
            except Exception as e:
                print(e)
        


        with open('{}{}.json'.format(MASSNICK_SAVE_LOC, ctx.guild.id), 'w') as fp:
            json.dump(oldNames, fp)


        await ctx.send("Names saved. use {}massunnick to revert everyones names back.".format(ctx.prefix))
        """
        for userId, dispName in oldNames.items():
            _id = int(userId)

            self.bot: commands.Bot
            member = await self.bot.get_guild(ctx.guild.id).fetch_member(_id)
            try:
                await member.edit(nick=dispName)
            except Exception as e:
                print(e)
        """

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def massunnick(self, ctx):
        # check if the server was mass-nicked
        file = "{}{}.json".format(MASSNICK_SAVE_LOC, ctx.guild.id)
        exists = os.path.isfile(file)

        if not exists:
            await ctx.send("This server did *not* suffer from a mass-nick.")
            return

        oldNames = {}
        with open('{}{}.json'.format(MASSNICK_SAVE_LOC, ctx.guild.id), 'r') as fp:
            print("Loading temp to ram...")
            oldNames = json.load(fp)

        print(oldNames)

        for userId, dispName in oldNames.items():
            _id = int(userId)

            self.bot: commands.Bot
            member = await self.bot.get_guild(ctx.guild.id).fetch_member(_id)
            try:
                await member.edit(nick=dispName)
            except Exception as e:
                print(e)
        await ctx.send("Everyone was freed.")
        os.remove(file)  


    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, member: discord.Member = None):
        if member is None:
            await ctx.send("Please provide the member you would like to unban.")
            return

        await member.unban()

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def timeban(self, ctx, member: discord.Member, time: int = 0):
        if time == 0:
            await ctx.send(
                "Please input the amount of time you would like to ban this user for. Example:"
            )
            await ctx.send("{}timeban <user> 4<h|m|s|d|w|y>".format(ctx.prefix))
            return

        to_secs = self.convert_to_seconds(time)
        await ctx.send(
            "Okay, I will ban {} for {}.".format(member.display_name, to_secs)
        )
        await member.ban()
        await asyncio.sleep(to_secs)
        # attempt to DM the user
        try:
            await member.send(
                "Your ban timer has been expired. You are able to rejoin {}.".format(
                    ctx.guild.name
                )
            )
            await member.unban()
        except:
            # we couldn't, just unban them without sending it
            await member.unban()

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason: str = None):
        await ctx.send("Kicked member: {} for: {}".format(member.display_name, reason))
        await member.kick(reason=reason)

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def purge(self, ctx, count: int = None):
        if count == None:
            usage = f"{ctx.prefix}purge <amount>"
            await ctx.send(usage)
            return

        try:
            await ctx.channel.purge(limit=count + 1)
            await asyncio.sleep(1)
            await ctx.send(f"Purged {count} messages from this channel.")
        except:
            return

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def echo(self, ctx, location: int = None, *, msg):
        usage = "{}echo <channel id> <msg>".format(ctx.prefix)
        if location == None:
            await ctx.send(usage)
            return

        try:
            channel = self.bot.get_channel(location)
            await channel.send(msg)
        except:
            await ctx.send(usage)
            return


async def setup(bot):
    await bot.add_cog(Admin(bot))
