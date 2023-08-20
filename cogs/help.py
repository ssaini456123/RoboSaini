import json

import discord
from discord.ext import commands
from utils.logger import logF


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        with open("templates/help.json") as helptmp:
            self.help_dict = json.load(helptmp)

        self.modules_list = self.help_dict["modules"]

    async def get_cmd_count(self, module_name: str = None):
        count = len(self.modules_list[module_name]["commands"])
        return count

    @commands.command()
    async def help(self, ctx, module_name: str = None):
        prefix = ctx.prefix

        embedColor = discord.Color.blurple()
        help_board = discord.Embed(color=embedColor)

        if module_name == None:
            help_board.add_field(
                name=f"List of available modules",
                value=f'``For help on a specific module, run {prefix}help "module_name"``',
                inline=False,
            )
            for i in self.modules_list:
                msg = f"**{i}**"
                cmd_count = await self.get_cmd_count(i)

                valmsg = f"┕━━━ {cmd_count} available command"
                if cmd_count > 1:
                    valmsg += "s"

                help_board.add_field(name=msg, value=f"`{valmsg}`", inline=True)

            await ctx.send(embed=help_board)
            return

        for i in self.modules_list:
            # make the search case insensitive
            module_raw_name = module_name.lower()

            # check if the module exists in the modules list
            if module_raw_name == i:
                # we have a match

                command_list = self.modules_list[module_raw_name]["commands"]

                # iterate through the commands in that given module
                for j in command_list:
                    # split our string into a list as such:
                    # [command_name, description]
                    spliced = j.split(" - ")
                    # logF(spliced)

                    # is our command whitelisted?
                    is_whitelisted = self.modules_list[module_raw_name]["whitelisted"]

                    # are we in the homeserver id?
                    homeserver_id = self.modules_list[module_raw_name]["homeserver_id"]

                    if is_whitelisted:
                        if homeserver_id == ctx.guild.id:
                            help_board.title = "[[Homeserver]] List of available commands for: `{}`".format(
                                module_raw_name.capitalize()
                            )
                            help_board.add_field(
                                name=f"{spliced[0]}",
                                value=f"``┕━ {spliced[1]}``",
                                inline=False,
                            )
                            break
                        else:
                            # do not display whitelisted commands in the help board period
                            continue

                    usage = spliced[2]
                    help_board.color = embedColor

                    padding = ""
                    if len(spliced[1]) > 47:
                        padding += "\n​"  # zero width space to make that command "disconnected" from the others, regardless of the length of the
                        # usage message.

                    help_board.title = "List of available commands for `{}`".format(
                        module_raw_name.capitalize()
                    )

                    help_board.add_field(
                        name=f"`{prefix}{usage}`",
                        value=f"``┕━━ {spliced[1]}``{padding}",
                        inline=False,
                    )
                await ctx.send(embed=help_board)
                return

        if module_raw_name not in self.modules_list:
            await ctx.send(
                f"*{ctx.author.name}*, The module **{module_raw_name}** does not exist..."
            )
            return


async def setup(bot):
    await bot.add_cog(Help(bot))
