from discord.ext import commands


class Event(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = self.bot.db

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        voice_state = member.guild.voice_client
        if voice_state is not None and len(voice_state.channel.members) == 1:
            await voice_state.disconnect()
            print("Left guild VC due to idleness")


async def setup(bot):
    await bot.add_cog(Event(bot))
