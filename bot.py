import discord
from discord.ext import commands

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='!')

    async def load_cogs(self):
        cog_files = [
            'roles',
            'lfg',
            'welcome',
            'moderation',
            'utility',
            'events',
            'levels',
            'economy',
            'logging'
        ]
        for cog in cog_files:
            self.load_extension(f'cogs.{cog}')

bot = MyBot()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

bot.run('your_token_here')
