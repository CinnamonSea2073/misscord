import discord
from discord.ui import Select, View
from discord.ext import commands, tasks
from discord.commands import Option, SlashCommandGroup, OptionChoice
import datetime
import main
from misskey import Misskey
import lib.sql as sql
import requests

l: list[discord.SelectOption] = []
SELECT_CONTENT_WARNING = [
    OptionChoice(name='コンテンツ警告指定する', value=True),
    OptionChoice(name='コンテンツ警告指定しない', value=False)
]
SELECT_LOCAL_ONLY = [
    OptionChoice(name='インスタンス限定で投稿する', value=True),
    OptionChoice(name='グローバル投稿する', value=False)
]

class helpselectView(View):
    @discord.ui.select(
        placeholder="表示するヘルプコマンド",
        options=[
            discord.SelectOption(
                    label="misskeyコマンド",
                    emoji="📰",
                    description="Misskeuの操作ができます。",
            ),
            discord.SelectOption(
                label="userコマンド",
                emoji="📚",
                description="登録したユーザー情報を操作するコマンドです。"),
            discord.SelectOption(
                label="設定コマンド",
                emoji="⚙",
                description="Ephemeral等を設定します"),
        ])
    async def select_callback(self, select: discord.ui.Select, interaction):
        embed = discord.Embed(
            title=f"helpコマンド：{select.values[0]}", color=0x1e90ff)
        if select.values[0] == "Misskeyコマンド":
            embed.add_field(
                name=f"misskeyを操作するコマンドです。",
                value=f"\
                    \n**・/misskey profile**\nプロフィールを取得して表示します。\
                    \n**・/misskey post**\nテキストを投稿します。\
                ")
        elif select.values[0] == "userコマンド":
            embed.add_field(
                name=f"登録しているmisskeyアカウントを管理するコマンドです。",
                value=f"\
                    \n**・/user controle**\n登録しているmisskeyアカウントを管理します。\
                ")
        elif select.values[0] == "設定コマンド":
            embed.add_field(
                name=f"Ephemeralなどを設定するコマンドです。",
                value=f"\
                    \n**・/setting ephemeral**\nコマンド使用履歴を確認できるようにするか設定します。\
                ")
        await interaction.response.edit_message(content=None, embed=embed, view=self)


class ReportModal(discord.ui.Modal):
    def __init__(self, select: str):
        super().__init__(title="バグ報告", timeout=300,)
        self.select = select

        self.content = discord.ui.InputText(
            label="バグの内容",
            style=discord.InputTextStyle.paragraph,
            placeholder="どのような状況でしたか？",
            required=True,
        )
        self.add_item(self.content)
        self.resalt = discord.ui.InputText(
            label="バグによって生じたこと",
            style=discord.InputTextStyle.paragraph,
            placeholder="例：インタラクションに失敗した、メッセージが大量に表示された等",
            required=True,
        )
        self.add_item(self.resalt)

    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.edit_message(content="読み込み中...")
        self.content = self.content.value
        self.resalt = self.resalt.value
        now = datetime.datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')
        try:
            embed = discord.Embed(
                title=f"バグ報告", color=0x1e90ff, description=now)
            embed.add_field(name="コマンド", value=self.select)
            embed.add_field(
                name="ユーザー", value=f"{interaction.user.name}\n{interaction.user.id}")
            embed.add_field(
                name="サーバー", value=f"{interaction.guild.name}\n{interaction.guild.id}")
            embed.add_field(name="\n内容", value=self.content)
            embed.add_field(name="詳細", value=f"```{self.resalt}```")

            channel = await main.sendChannel(1140181925814882320)
            await channel.send(embed=embed)
            await interaction.edit_original_message(content=f"不具合を送信しました！ご協力ありがとうございます！\nbugTrackName:{self.content}", view=None)
            return
        except:
            print("おい管理者！エラーでてんぞこの野郎！！！！")
            await interaction.edit_original_message(content=f"送信できませんでしたが、管理者にログを表示しました。修正までしばらくお待ちください", view=None)
            raise


class bugselectView(View):
    @discord.ui.select(
        placeholder="どのコマンドで不具合が出ましたか？",
        options=[
            discord.SelectOption(
                    label="/misskey",
                    description="help, profile等",),
            discord.SelectOption(
                label="/user",
                description="controle等",),
            discord.SelectOption(
                label="/setting",
                description="ephemeral等"),
        ])
    async def select_callback(self, select: discord.ui.Select, interaction):
        print(str(select.values[0]))
        await interaction.response.send_modal(ReportModal(select.values[0]))


class ReplayModal(discord.ui.Modal):
    def __init__(self, post_id, post_user_name):
        super().__init__(title="リプライ")
        self.post_id = post_id
        self.post_user_name = post_user_name

        self.text = discord.ui.InputText(
            label="返信するテキストを入力してね",
            style=discord.InputTextStyle.short,
            required=True,
        )
        self.add_item(self.text)

    async def callback(self, interaction: discord.Interaction) -> None:
        user_data = sql.User.get_user_list(user_id=interaction.user.id)
        user_data = user_data[0]
        mk = Misskey(user_data.instance, i=user_data.api_key)
        data = mk.notes_create(text=self.text.value, reply_id=self.post_id)
        post_id = data["createdNote"]["id"]
        profile = mk.i()
        embed = discord.Embed(title=f"Replay @{self.post_user_name} by {profile['name']}", description='@'+profile['username']+'@'+user_data.instance)
        embed.set_thumbnail(url=profile['avatarUrl'])
        embed.add_field(name="投稿内容", value=self.text.value)
        view = ActionButtontView(post_id=post_id, post_user_name=profile['name'])
        await interaction.response.send_message(embed=embed, view=view, ephemeral=sql.Ephemeral.is_ephemeral(interaction.guild_id))

class RepostModal(discord.ui.Modal):
    def __init__(self, post_id, post_user_name):
        super().__init__(title="リポスト")
        self.post_id = post_id
        self.post_user_name = post_user_name

        self.text = discord.ui.InputText(
            label="リポストテキストを入力してね（必須ではありません）",
            required=False,
            style=discord.InputTextStyle.short,
        )
        self.add_item(self.text)

    async def callback(self, interaction: discord.Interaction) -> None:
        print(self.text)
        user_data = sql.User.get_user_list(user_id=interaction.user.id)
        user_data = user_data[0]
        mk = Misskey(user_data.instance, i=user_data.api_key)
        try:
            data = mk.notes_create(text=self.text.value, renote_id=self.post_id)
        except:
            data = mk.notes_create(text=None, renote_id=self.post_id)
        post_id = data["createdNote"]["id"]
        profile = mk.i()
        embed = discord.Embed(title=f"Repost @{self.post_user_name} by {profile['name']}", description='@'+profile['username']+'@'+user_data.instance)
        embed.set_thumbnail(url=profile['avatarUrl'])
        if self.text:
            embed.add_field(name="投稿内容", value=self.text.value)
        view = ActionButtontView(post_id=post_id, post_user_name=profile['name'])
        await interaction.response.send_message(embed=embed, view=view, ephemeral=sql.Ephemeral.is_ephemeral(interaction.guild_id))

class ReactionModal(discord.ui.Modal):
    def __init__(self, post_id, post_user_name):
        super().__init__(title="リアクション")
        self.post_id = post_id
        self.post_user_name = post_user_name

        self.text = discord.ui.InputText(
            label="絵文字、またはコロンで囲まれたカスタム絵文字名を入力",
            style=discord.InputTextStyle.short,
        )
        self.add_item(self.text)

    async def callback(self, interaction: discord.Interaction) -> None:
        print(self.text)
        user_data = sql.User.get_user_list(user_id=interaction.user.id)
        user_data = user_data[0]
        mk = Misskey(user_data.instance, i=user_data.api_key)
        view = View()
        view.add_item(ReactionCancelButton(self.post_id))
        try:
            data = mk.notes_reactions_create(note_id=self.post_id, reaction=self.text.value)
            await interaction.response.send_message(content="リアクションしました", view=view, ephemeral=True)
        except:
            await interaction.response.send_message(content="エラーが発生しました。二つの絵文字が入力されたか、すでにリアクション済の可能性があります。", view=view, ephemeral=True)

class ReactionCancelButton(discord.ui.Button):
    def __init__(self, post_id):
        super().__init__(label="リアクションを取り消す", style=discord.ButtonStyle.green)
        self.post_id = post_id

    async def callback(self, interaction: discord.Interaction):
        user_data = sql.User.get_user_list(user_id=interaction.user.id)
        if user_data == []:
            embed = discord.Embed(title=f"<@{interaction.user.id}> 事前にユーザーを登録してください。")
            await interaction.response.send_message(embed=embed, ephemeral=sql.Ephemeral.is_ephemeral(interaction.guild_id))
            return
        mk = Misskey(user_data[0].instance)
        mk.token = user_data[0].api_key
        mk.notes_reactions_delete(self.post_id)
        await interaction.response.edit_message(content="リアクションを取り消しました。")

class ActionButtontView(View):
    def __init__(self, post_id, post_user_name):
        super().__init__()
        self.post_id = post_id
        self.post_user_name = post_user_name

    @discord.ui.button(emoji="<:replay:1140262214343868436>")
    async def replay(self, _: discord.ui.Button, interaction: discord.Interaction):
        user_data = sql.User.get_user_list(user_id=interaction.user.id)
        if user_data == []:
            embed = discord.Embed(title=f"<@{interaction.user.id}> 事前にユーザーを登録してください。")
            await interaction.response.send_message(embed=embed, ephemeral=sql.Ephemeral.is_ephemeral(interaction.guild_id))
            return
        await interaction.response.send_modal(ReplayModal(post_id=self.post_id, post_user_name=self.post_user_name))
    
    @discord.ui.button(emoji="<:Repost:1140262236900818984>")
    async def renote(self, _: discord.ui.Button, interaction: discord.Interaction):
        user_data = sql.User.get_user_list(user_id=interaction.user.id)
        if user_data == []:
            embed = discord.Embed(title=f"<@{interaction.user.id}> 事前にユーザーを登録してください。")
            await interaction.response.send_message(embed=embed, ephemeral=sql.Ephemeral.is_ephemeral(interaction.guild_id))
            return
        await interaction.response.send_modal(RepostModal(post_id=self.post_id, post_user_name=self.post_user_name))

    @discord.ui.button(emoji="<:Plus:1140262257234804816>")
    async def reaction(self, _: discord.ui.Button, interaction: discord.Interaction):
        user_data = sql.User.get_user_list(user_id=interaction.user.id)
        if user_data == []:
            embed = discord.Embed(title=f"<@{interaction.user.id}> 事前にユーザーを登録してください。")
            await interaction.response.send_message(embed=embed, ephemeral=sql.Ephemeral.is_ephemeral(interaction.guild_id))
            return
        await interaction.response.send_modal(ReactionModal(post_id=self.post_id, post_user_name=self.post_user_name))

    @discord.ui.button(emoji="<:Heart:1140262284925612073>")
    async def favorites(self, _: discord.ui.Button, interaction: discord.Interaction):
        user_data = sql.User.get_user_list(user_id=interaction.user.id)
        if user_data == []:
            embed = discord.Embed(title=f"<@{interaction.user.id}> 事前にユーザーを登録してください。")
            await interaction.response.send_message(embed=embed, ephemeral=sql.Ephemeral.is_ephemeral(interaction.guild_id))
            return
        mk = Misskey(user_data[0].instance)
        mk.token = user_data[0].api_key
        mk.notes_favorites_create(self.post_id)
        view = View()
        view.add_item(FavoritesCancelButton(self.post_id))
        await interaction.response.send_message(content="お気に入り登録しました。", ephemeral=True, view=view)

class FavoritesCancelButton(discord.ui.Button):
    def __init__(self, post_id):
        super().__init__(label="お気に入りを取り消す", style=discord.ButtonStyle.green)
        self.post_id = post_id

    async def callback(self, interaction: discord.Interaction):
        user_data = sql.User.get_user_list(user_id=interaction.user.id)
        if user_data == []:
            embed = discord.Embed(title=f"<@{interaction.user.id}> 事前にユーザーを登録してください。")
            await interaction.response.send_message(embed=embed, ephemeral=sql.Ephemeral.is_ephemeral(interaction.guild_id))
            return
        mk = Misskey(user_data[0].instance)
        mk.token = user_data[0].api_key
        mk.notes_favorites_delete(self.post_id)
        await interaction.response.edit_message(content="お気に入りを取り消しました。")

class MisskeyCog(commands.Cog):

    def __init__(self, bot):
        print('misskey_init')
        self.bot = bot

    misskey = SlashCommandGroup('misskey', 'test')
    
    @misskey.command(name='help', description='Misscordのヘルプです。')
    async def chelp(self, ctx):
        embed = discord.Embed(title=f"helpコマンド：misskeyコマンド", color=0x1e90ff)
        embed.add_field(
            name=f"misskeyを操作するコマンドです。",
            value=f"\
                \n**・/misskey profile**\nプロフィールを取得して表示します。\
                \n**・/misskey post**\nテキストを投稿します。\
            ")
        view = helpselectView(timeout=300, disable_on_timeout=True)
        # レスポンスで定義したボタンを返す
        await ctx.respond("確認したいコマンドのジャンルを選択してください", embed=embed, view=view, ephemeral=sql.Ephemeral.is_ephemeral(ctx.guild.id))

    @misskey.command(name='report', description='不具合報告はこちらから！')
    async def report(self, ctx):

        view = bugselectView()
        await ctx.respond(view=view, ephemeral=sql.Ephemeral.is_ephemeral(ctx.guild.id))

    @misskey.command(name='profile', description='プロフィール')
    async def code(
            self, 
            ctx: discord.ApplicationContext, 
            ):
        
        user_data = sql.User.get_user_list(user_id=ctx.author.id)
        if user_data == []:
            embed = discord.Embed(title=f"エラー・事前にユーザーを登録してください。")
            await ctx.respond(embed=embed, ephemeral=sql.Ephemeral.is_ephemeral(ctx.guild_id))

        print(user_data)
        user_data = user_data[0]
        mk = Misskey(user_data.instance)
        mk.token = user_data.api_key
        profile = mk.i()
        embed = discord.Embed(title=f"{profile['name']} さんのプロフィール", description='@'+profile['username']+'@'+user_data.instance)
        embed.set_thumbnail(url=profile['avatarUrl'])
        embed.add_field(name="ステータス", value=profile['onlineStatus'])
        await ctx.respond(embed=embed, ephemeral=sql.Ephemeral.is_ephemeral(ctx.guild_id))

    @misskey.command(name='post', description='ノートを投稿します')
    async def code(
            self, 
            ctx: discord.ApplicationContext,
            text: Option(str, name="テキスト", description="投稿する内容", required=True),
            is_content_warning: Option(bool, name="コンテンツ警告指定", choices=SELECT_CONTENT_WARNING, description="コンテンツ警告として指定するか選択します。未指定の場合は指定しません。", default=False),
            is_local_only : Option(bool, name="投稿範囲", choices=SELECT_LOCAL_ONLY, description="投稿する範囲を指定します。未指定の場合はグローバルで投稿します。", default=False),
            ):
        
        user_data = sql.User.get_user_list(user_id=ctx.author.id)
        if user_data == []:
            embed = discord.Embed(title=f"エラー・事前にユーザーを登録してください。")
            await ctx.respond(embed=embed, ephemeral=sql.Ephemeral.is_ephemeral(ctx.guild_id))

        user_data = user_data[0]
        mk = Misskey(user_data.instance)
        mk.token = user_data.api_key
        """
        data = requests.post(
            f'http://{user_data.instance}/api/notes/create', 
            json={
                'visibility': 'public',
                'visibleUserIds': [],
                'text': text,
                'localOnly': is_local_only,
            })
        """
        data = mk.notes_create(text=text, visibility='public', local_only=is_local_only)
        post_id = data["createdNote"]["id"]
        profile = mk.i()
        embed = discord.Embed(title=f"@{profile['username']}", description=text)
        embed.set_thumbnail(url=profile['avatarUrl'])
        view = ActionButtontView(post_id=post_id, post_user_name=profile['username'])
        await ctx.respond(embed=embed, view=view, ephemeral=sql.Ephemeral.is_ephemeral(ctx.guild_id))

def setup(bot):
    bot.add_cog(MisskeyCog(bot))
