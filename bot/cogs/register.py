import discord
from discord.ui import Select, View, Button, Modal
from discord.ext import commands
from discord import Option, SlashCommandGroup
import aiohttp
import lib.sql as SQL
from misskey import Misskey
import requests
import uuid

l: list[discord.SelectOption] = []

# UIDを聞くモーダル


class UidModal(discord.ui.Modal):
    def __init__(self, ctx):
        super().__init__(title="ユーザー登録")
        self.ctx = ctx

        self.instance = discord.ui.InputText(
            label="インスタンスを入力してください。",
            style=discord.InputTextStyle.short,
            placeholder="example.com",
            required=True,
        )
        self.api_key = discord.ui.InputText(
            label="api_keyを入力してください。",
            style=discord.InputTextStyle.short,
            required=True,
        )
        self.add_item(self.instance)
        self.add_item(self.api_key)

    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.edit_message(content=f"処理中です...", embed=None, view=None)
        try:
            mk = Misskey(self.instance.value, i=self.api_key.value)
            profile = mk.i()
            print(profile)
            await uid_set(self.ctx, self.api_key.value, self.instance.value, profile['username'])
        except Exception as e:
            print(e)
            await interaction.edit_original_message(content=f"えらー！", embed=None, view=None)
            return
        await interaction.edit_original_message(content="登録しました！", view=None)

# モーダルを表示させるボタン


class UidModalButton(discord.ui.Button):
    def __init__(self, ctx):
        super().__init__(label="APIKeyから登録する", style=discord.ButtonStyle.green)
        self.ctx = ctx

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(UidModal(self.ctx))
        print(
            f"==========\n実行者:{interaction.user.name}\n鯖名:{interaction.guild.name}\ncontrole - UIDモーダル表示")

# MiAauthのモーダルを表示させるボタン


class MiAuthModalButton(discord.ui.Button):
    def __init__(self, ctx):
        super().__init__(label="ブラウザから登録する", style=discord.ButtonStyle.green)
        self.ctx = ctx

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(modal=MiAuthModal(self.ctx))

# MiAuthのモーダル
class MiAuthModal(discord.ui.Modal):
    def __init__(self, ctx):
        super().__init__(title="インスタンスの入力")
        self.ctx = ctx

        self.instance = discord.ui.InputText(
            label="インスタンスを入力してください。",
            style=discord.InputTextStyle.short,
            placeholder="example.com",
            required=True,
        )
        self.add_item(self.instance)

    async def callback(self, interaction: discord.Interaction) -> None:
        user_miauth_id = uuid.uuid4()
        print(user_miauth_id)
        url=f"[miAuth](https://{self.instance.value}/miauth/{user_miauth_id}?name=misscord&icon=https://cdn.discordapp.com/attachments/1140183778959036518/1140184159491477545/misscord_icon.png&permission=read:account,\write:account,read:blocks,write:blocks,read:drive,write:drive,read:favorites,write:favorites,read:following,write:following,read:messaging,write:messaging,read:mutes,write:mutes,write:notes,read:notifications,write:notifications,write:reactions,write:votes,read:pages,write:pages,write:page-likes,read:page-likes,write:gallery-likes,read:gallery-likes)"
        embed = discord.Embed(title="MiAuthを使った登録", description="MiAuthは、APIキーを自動で作成する公式の仕組みです。misskeyにアクセスしてユーザーを登録します。")
        embed.add_field(name="手順1", value=f"以下のURLからmisskeyにアクセス\n{url}")
        embed.add_field(name="手順2", value="misskeyの指示に従ったあと、ボタンを押して登録")
        embed.set_footer(text="misskeyのサイトにアクセスできない場合、インスタンスが間違っている可能性があります。その場合、やり直してください。")
        view = View()
        view.add_item(MiAuthRegisterButton(ctx=self.ctx, instance=self.instance.value, user_miauth_id=user_miauth_id))
        await interaction.response.edit_message(content=None, embed=embed, view=view)

class MiAuthRegisterButton(discord.ui.Button):
    def __init__(self, ctx, instance, user_miauth_id):
        super().__init__(label="登録する", style=discord.ButtonStyle.green)
        self.ctx = ctx
        self.instance = instance
        self.user_miauth_id = user_miauth_id

    async def callback(self, interaction: discord.Interaction):
        try:
            data = requests.post(f'https://{self.instance}/api/miauth/{self.user_miauth_id}/check').json()
            mk = Misskey(self.instance, i=data["token"])
            profile = mk.i()
            print(profile)
            await uid_set(self.ctx, data["token"], self.instance, profile['username'])
            await interaction.response.edit_message(content="登録しました！", embed=None, view=None)
        except Exception as e:
            print(e)
            await interaction.response.edit_message(content="エラーが発生しました。もう一度やり直してください。")

# 本当にUIDを削除するかどうか聞くボタン


class isDeleteEnterButton(View):
    def __init__(self, user_data: SQL.User, ctx):
        super().__init__(timeout=300, disable_on_timeout=True)
        self.ctx = ctx
        self.user_data = user_data

    @discord.ui.button(label="削除する", style=discord.ButtonStyle.red)
    async def callback(self, button, interaction: discord.Interaction):
        try:
            await uid_del(self.ctx, self.user_data.api_key)
        except:
            await interaction.response.edit_message(content=f"{self.user_data.user_name}を何らかの理由で削除できませんでした。\nよろしければ、botのプロフィールからエラーの報告をお願いします。", embed=None, view=None)
            raise
        self.clear_items()
        await interaction.response.edit_message(content=f"削除しました。", embed=None, view=self)

    @discord.ui.button(label="キャンセルする", style=discord.ButtonStyle.green)
    async def no_callback(self, button, interaction: discord.Interaction):
        self.clear_items()
        await interaction.response.edit_message(content="削除がキャンセルされました", view=self)

# UIDを登録する関数


async def uid_set(ctx, api_key, instance, user_name):
    userData = SQL.User(ctx.author.id, api_key, instance, user_name)
    SQL.User.insert_user(userData)
    return

# UIDを削除する関数


async def uid_del(ctx, api_key):
    serverId = ctx.guild.id
    SQL.User.delete_user(ctx.author.id, api_key)
    return api_key

async def getEmbed(ctx):
    serverId = ctx.guild.id
    view = View(timeout=300, disable_on_timeout=True)

    # もしuserに当てはまるUIDが無ければ終了
    uidList = SQL.User.get_user_list(ctx.author.id)
    embed = discord.Embed(
        title=f"登録情報",
        description=f"{len(uidList)}個のユーザーデータが登録されています。",
        color=0x1e90ff,
    )
    for v in uidList:
        embed.add_field(
            inline=False, name=f"ユーザー名・{v.user_name}", value=f"インスタンス: {v.instance}")
    return embed


class select_user_pulldown(discord.ui.Select):
    def __init__(self, ctx, selectOptions: list[discord.SelectOption], user_data: list[SQL.User]):
        super().__init__(placeholder="削除するユーザデータを選択してください", options=selectOptions)
        self.ctx = ctx
        self.user_data = user_data

    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="削除しようとしているユーザデータ", description=f"インスタンス:{self.values[0]}\nユーザ名:{[i for i in self.user_data if i.instance == self.values[0]][0].user_name}", color=0x1e90ff, )
        await interaction.response.edit_message(content=f"**本当に削除しますか？**\n", view=isDeleteEnterButton([i for i in self.user_data if i.instance == self.values[0]][0], self.ctx), embed=embed)

class userListCog(commands.Cog):

    def __init__(self, bot):
        print('uidList初期化')
        self.bot = bot

    user = SlashCommandGroup('user', 'test')

    @user.command(name="control", description="ユーザーデータの操作パネルを開きます。")
    async def user_control(
            self,
            ctx: discord.ApplicationContext,
    ):
        try:
            embed = await getEmbed(ctx)
            select_options: list[discord.SelectOption] = []
            userData = SQL.User.get_user_list(ctx.author.id)
            if userData == []:
                view = View(timeout=300, disable_on_timeout=True)
                button = UidModalButton(ctx)
                view.add_item(button)
                view.add_item(MiAuthModalButton(ctx=ctx))
                await ctx.respond(content="データが登録されていません。下のボタンから登録してください。", view=view, ephemeral=True)
                return
            for v in userData:
                select_options.append(
                    discord.SelectOption(label=v.user_name, value=v.instance))
            view = View(timeout=300, disable_on_timeout=True)
            view.add_item(select_user_pulldown(ctx, select_options, userData))
            view.add_item(UidModalButton(ctx))
            view.add_item(MiAuthModalButton(ctx=ctx))
            await ctx.respond(embed=embed, view=view, ephemeral=True)
        except:
            view = View()
            button = UidModalButton(ctx)
            view.add_item(button)
            view.add_item(MiAuthModalButton(ctx=ctx))
            await ctx.respond(content="ユーザーが登録されていません。下のボタンから登録してください。", view=view, ephemeral=True)
            return


def setup(bot):
    bot.add_cog(userListCog(bot))
