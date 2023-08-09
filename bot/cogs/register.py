import discord
from discord.ui import Select, View, Button, Modal
from discord.ext import commands
from discord import Option, SlashCommandGroup
import aiohttp
import lib.sql as SQL
from misskey import Misskey

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
            await uid_set(self.ctx, self.api_key.value, self.instance.value, profile['name'])
        except Exception as e:
            print(e)
            await interaction.edit_original_message(content=f"えらー！", embed=None, view=None)
            return
        await interaction.edit_original_message(content="登録しました！", view=None)

# モーダルを表示させるボタン


class UidModalButton(discord.ui.Button):
    def __init__(self, ctx):
        super().__init__(label="データを登録する", style=discord.ButtonStyle.green)
        self.ctx = ctx

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(UidModal(self.ctx))
        print(
            f"==========\n実行者:{interaction.user.name}\n鯖名:{interaction.guild.name}\ncontrole - UIDモーダル表示")

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
                await ctx.respond(content="データが登録されていません。下のボタンから登録してください。", view=view, ephemeral=SQL.Ephemeral.is_ephemeral(ctx.guild_id))
                return
            for v in userData:
                select_options.append(
                    discord.SelectOption(label=v.user_name, value=v.instance))
            view = View(timeout=300, disable_on_timeout=True)
            view.add_item(select_user_pulldown(ctx, select_options, userData))
            view.add_item(UidModalButton(ctx))
            await ctx.respond(embed=embed, view=view, ephemeral=SQL.Ephemeral.is_ephemeral(ctx.guild_id))
        except:
            view = View()
            button = UidModalButton(ctx)
            view.add_item(button)
            await ctx.respond(content="ユーザーが登録されていません。下のボタンから登録してください。", view=view, ephemeral=SQL.Ephemeral.is_ephemeral(ctx.guild_id))
            return


def setup(bot):
    bot.add_cog(userListCog(bot))
