import time
import random
import json
import wavelink

from discord.ext import commands

from wavelink.ext import spotify
from wavelink.ext.spotify import SpotifyTrack

from utils.message import InvalidCommandUsageEmbed, QuickEmbed


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        with open("config.json") as conf:
            config = json.load(conf)
            self.lavalink_pwd = config["lavalink_pwd"]
            self.lavalink_port = config["lavalink_port"]
            self.lavalink_host = config["lavalink_host"]

            self.spotify_client_id = config["spotify_client_id"]
            self.spotify_client_secret = config["spotify_client_secret"]

        print("{} Connecting wavelink nodes...")
        bot.loop.create_task(self.connect_nodes())
        print("{} Done.")

    async def connect_nodes(self):
        print("port={}".format(self.lavalink_port))
        print("host={}".format(self.lavalink_host))
        await self.bot.wait_until_ready()

        _spotify = spotify.SpotifyClient(
            client_id=self.spotify_client_id, client_secret=self.spotify_client_secret
        )
        node: wavelink.Node = wavelink.Node(
            uri="http://{}:{}".format(self.lavalink_host, self.lavalink_port),
            password=self.lavalink_pwd,
            retries=1,
        )

        await wavelink.NodePool.connect(client=self.bot, nodes=[node], spotify=_spotify)

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node):
        print("Wavelink => {} - stats => {}".format(node.identifier, node.stats))

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, player: wavelink.Player, track, reason):
        isEmpty = player.queue.is_empty

        if not isEmpty:
            new = await player.queue.get_wait()
            await player.play(track=new)
        else:
            await player.stop()

    @commands.command()
    async def play(self, ctx, *, search: wavelink.YouTubeTrack = None):
        random.seed(time.time())

        if search == None:
            await InvalidCommandUsageEmbed(
                ctx=ctx, description="play <song> *(Youtube only!)*"
            ).send()
            return

        if not ctx.voice_client:
            try:
                vc: wavelink.Player = await ctx.author.voice.channel.connect(
                    cls=wavelink.Player
                )
            except Exception as err:
                player_errors = [
                    "You must join a VC before playing a song.",
                    "You try to play a song before joining a VC. It was ineffective.",
                ]

                r_arr = random.choice(player_errors)

                await ctx.send(":warning: {}".format(r_arr))
                return
        else:
            vc: wavelink.Player = ctx.voice_client

        vc.autoplay = True

        if vc.queue.is_empty and not vc.is_playing():
            duration = search.duration
            convert = time.strftime("%H:%M:%S", time.gmtime(duration))

            await ctx.send(
                "🎵 Now playing: `{}` ({}) - {}".format(
                    search.title, convert, ctx.message.author.mention
                )
            )
            await vc.play(search)

        else:
            await vc.queue.put_wait(item=search)
            await ctx.send("**{}** has been added to the queue.".format(search))

    @commands.command()
    async def queue(self, ctx):
        vc: wavelink.Player = ctx.voice_client
        errNoSong = "There are currently no songs in the queue."

        if vc == None:
            await ctx.send(errNoSong)

        iters = 0

        finished: bool = False

        msg = ""
        total = vc.queue.__len__()

        while not finished:
            for i in vc.queue:
                if i.length <= 0:
                    await ctx.send(errNoSong)
                    return

                iters += 1
                msg += "**{}.** {}\n".format(iters, i.title)

            if iters == 0:
                # dont send the message if our queue is empty

                await ctx.send(errNoSong)
                return

            finished = True
            break

        await QuickEmbed(
            ctx=ctx,
            title=":notes: List of songs in the queue (**{}** songs in total) :notes:".format(
                total
            ),
            description=msg,
        ).send()
        return

    @commands.command()
    async def connect(self, ctx):
        vc: wavelink.Player = await ctx.author.voice.channel.connect(
            cls=wavelink.Player
        )
        await ctx.send("Player connected.")

    @commands.command()
    async def disconnect(self, ctx):
        if not ctx.voice_client:
            return
        else:
            vc: wavelink.Player = ctx.voice_client

        await ctx.send("Player disconnected.")
        await vc.disconnect()

    @commands.command()
    async def stop(self, ctx):
        vc: wavelink.Player = ctx.voice_client
        await ctx.send(":pause_button: Music player paused.")
        await vc.pause()

    @commands.command()
    async def resume(self, ctx):
        vc: wavelink.Player = ctx.voice_client
        if vc.is_paused:
            await vc.resume()
        else:
            await ctx.send("**The player wasnt even paused to begin with...**")

    @commands.command()
    async def current(self, ctx):
        vc: wavelink.Player = ctx.voice_client
        track = vc.track

        if track == None:
            await ctx.send("There is currently nothing playing.")
            return

        await ctx.send("We are currently listening to: **{}**".format(vc.track))

    @commands.command()
    async def skip(self, ctx):
        vc: wavelink.Player = ctx.voice_client

        if not vc.queue.is_empty:
            new = vc.queue[0]

            duration = new.duration
            convert = time.strftime("%H:%M:%S", time.gmtime(duration))

            await vc.stop()

            await ctx.send("Skipped...")
            await ctx.send(
                "🎵 Now playing: `{}` ({}) - {}".format(
                    new.title, convert, ctx.message.author.mention
                )
            )

        else:
            await vc.stop()
            await ctx.send("The queue is empty.")


async def setup(bot):
    await bot.add_cog(Music(bot))
