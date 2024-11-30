import asyncio
import json
import os

import discord
import asyncpg
from discord.ext import commands
from utils.logger import *

# RoboSaini 2

BANNER = """

{}  _____       _____       _       _  {}
{} |  __ \     / ____|     (_)     (_) {}
{} | |__) |   | (___   __ _ _ _ __  _  {}
{} |  _  /     \___ \ / _` | | '_ \| | {}
{} | | \ \ _   ____) | (_| | | | | | | {}
{} |_|  \_(_) |_____/ \__,_|_|_| |_|_| {}

{}Author: https://github.com/terrain123456{}
"""

for i in BANNER.splitlines():
    if i == "":
        continue

    logF(i.format(color_green, color_reset))

print("\n\n")

TMP_DIR = "local/"
SONG_DUMP_PATH = "{}songs.txt".format(TMP_DIR)


class RoboSaini:
    def __init__(self):
        with open("config.json") as config:
            data = json.load(config)
            self.bot_pwd = data["bot_pwd"]
            self.bot_prefix = data["bot_prefix"]

            self.db_user = data["db_user"]
            self.db_pwd = data["db_password"]
            self.db_dbName = data["database"]
            self.db_host = data["host"]

        self.cog_list = [
            "cogs.help",
            "cogs.event",
            "cogs.admin",
            "cogs.wikipedia",
            "cogs.clippy",
            "cogs.time",
            "cogs.starboard",
            "cogs.ai",
            "cogs.music",
            "cogs.image"
        ]
        self.intents = discord.Intents.all()

        self.bot = commands.Bot(
            command_prefix=self.bot_prefix, case_insensitive=False, intents=self.intents
        )

    async def setup_cogs(self):
        for cog in self.cog_list:
            try:
                await self.bot.load_extension(cog)
                logF(f"{cog} Initialized.")
            except Exception as err:
                # cog didn't load properly, write out a warning with the new term color module
                logErr(f"{err}")

    async def begin_port(self, pool: asyncpg.connection.Connection):
        files = os.listdir("sql-scripts")

        for f in files:
            p = "sql-scripts/" + f
            with open(p) as sqlFile:
                read = sqlFile.read()
                await pool.execute(read)

        print("Tables initialized")

    async def run(self):
        async with self.bot as bot:
            # override the default help command (done in the actual cog init)
            bot.remove_command("help")

            try:
                # connect to DB
                db = await asyncpg.connect(
                    user=self.db_user,
                    password=self.db_pwd,
                    database=self.db_dbName,
                    host=self.db_host,
                )
                await self.begin_port(db)

                bot.db = db
            except:
                print("DB Disabled. Some modules will NOT work.")

            await self.setup_cogs()

            logF("R. Saini started.")
            print("")

            await bot.start(self.bot_pwd)


r = RoboSaini()
asyncio.run(r.run())
