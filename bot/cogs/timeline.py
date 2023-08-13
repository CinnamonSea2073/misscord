import discord
from discord.ui import Select, View
from discord.ext import commands, tasks
from discord.commands import Option, SlashCommandGroup, OptionChoice
import datetime
import main
from misskey import Misskey
import lib.sql as sql
import asyncio
import cogs.command as command
import time

class TimelineCog(commands.Cog):

    def __init__(self, bot):
        print('timeline_init')
        self.bot = bot

    timeline = SlashCommandGroup('timeline', 'test')
    
    @timeline.command(name='reload', description='タイムラインをリロードします（最大10件）。初めてのリロードでは、1日前からの投稿を取得します。')
    async def reload(
            self, 
            ctx: discord.ApplicationContext,
            ):
        
        try:
            channel = sql.channel.get_channel(ctx.guild_id)
            channel_id = channel[0]
            api_key = channel[1]
            instance = channel[2]
        except ValueError as e:
            await ctx.respond(content="通知チャンネルが設定されていません。管理者に連絡して設定してもらってください。```/setting channel```で設定できます。")
            return

        messageble_channel = self.bot.get_partial_messageable(channel_id)

        mk = Misskey(instance)
        mk.token = api_key

        try:
            sinceId = sql.notes.get_notes_channel(ctx.guild_id)
            sinceData = 0
        except:
            sinceId = '0'
            sinceData = int(time.time()) - 86400

        data = mk.notes_local_timeline(limit=10, since_id=sinceId, since_date=sinceData, with_files=False)
        print(data)

        for index, note in enumerate(data):
            asyncio.sleep(5)
            if note['text'] == None:
                continue
            embed = discord.Embed(title=f"@{note['user']['username']}", description=note['user']['onlineStatus'])
            embed.set_thumbnail(url=note['user']['avatarUrl'])
            embed.add_field(name="投稿内容", value=note['text'], inline=False)
            try:
                embed.add_field(name="リアクション", value=", ".join([f'{k}:{v}' for k, v in note['reactions'].items()]), inline=False)
            except:
                pass
            try:
                for image_url in note['files']:
                    embed.set_image(url=image_url['url'])
            except:
                pass
            embed.set_footer(text=note['createdAt'])
            view = command.ActionButtontView(post_id=note['id'], post_user_name=note['user']['username'])
            await messageble_channel.send(embed=embed, view=view)

            if index == len(data)-1:
                sql.notes.set_notes_channel(ctx.guild_id, notes_id=note['id'])
                return
        
        await ctx.respond(content="これ以上新しい投稿はありません。", ephemeral=True)


def setup(bot):
    bot.add_cog(TimelineCog(bot))
