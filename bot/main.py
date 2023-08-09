import discord
from discord.ext import commands
import os
import asyncio

intents = discord.Intents.default()
intents.guilds = True
bot = commands.AutoShardedBot(intents=intents)
# debug_guilds=[879288794560471050]
TOKEN = os.getenv(f"TOKEN")

path = "./cogs"


@bot.event
async def on_application_command_error(ctx: discord.ApplicationContext, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.respond(error)
        # traceback.format_exc())
        await bot.get_partial_messageable(1009731664412426240).send(error)
    elif isinstance(error, commands.MissingPermissions):
        await ctx.respond(content="BOT管理者限定コマンドです", ephemeral=True)
    else:
        raise error

@bot.event
async def on_guild_join(guild: discord.Guild):
    print(f"新規導入サーバー: {guild.name}")

@bot.event
async def on_ready():
    print(f"Bot名:{bot.user} On ready!!")
    await guildsCount()


async def sendChannel(id) -> discord.PartialMessageable:
    channel: discord.PartialMessageable = bot.get_partial_messageable(id)
    return channel


async def guildsCount():
    await asyncio.sleep(10)  # 複数のBOTを同時に再起動するときにちょっとあけとく
    await bot.change_presence(activity=discord.Game(name=f"Misskeyをプレイ中 / {'n'}サーバーで稼働中(累計)",))

bot.load_extensions(
    # 'cogs.wish_bata',
    # 'cogs.uidlist_bata',
    'cogs.command',
    'cogs.setting',
    'cogs.register',
    store=False
)

bot.run(TOKEN)
