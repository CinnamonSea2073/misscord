import discord
from discord.ui import Select, View
from discord.ext import commands, tasks
from discord.commands import Option, SlashCommandGroup, OptionChoice
import datetime
import main
from misskey import Misskey
import lib.sql as sql

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
        placeholder="表示するヘルプコマンドを指定してね",
        options=[
            discord.SelectOption(
                    label="メインコマンド",
                    emoji="📰",
                    description="原神ステータスを確認できます。",
            ),
            discord.SelectOption(
                label="UIDリストコマンド",
                emoji="📚",
                description="忘れがちなUIDを保存してくれるコマンドです。"),
            discord.SelectOption(
                label="祈願コマンド",
                emoji="✨",
                description="いわゆるガチャシミュレーターです。"),
            discord.SelectOption(
                label="便利コマンド",
                emoji="🧰",
                description="今日の日替わり秘境など"),
            discord.SelectOption(
                label="聖遺物スコア計算コマンド",
                emoji="🧮",
                description="スコアを簡単に計算します"),
            discord.SelectOption(
                label="通知コマンド",
                emoji="📢",
                description="樹脂などが溢れる前に通知します"),
            discord.SelectOption(
                label="設定コマンド",
                emoji="⚙",
                description="通知チャンネルなどを設定します"),
        ])
    async def select_callback(self, select: discord.ui.Select, interaction):
        embed = discord.Embed(
            title=f"helpコマンド：{select.values[0]}", color=0x1e90ff)
        if select.values[0] == "メインコマンド":
            print(
                f"help - メインコマンド\n実行者:{interaction.user.name}\n鯖名:{interaction.guild.name}")
            embed.add_field(
                name=f"このbotのメインとなるコマンドです。",
                value=f"\
                    \n**・/genshinstat get**\n自分以外が見ることができない状態で原神のステータスを取得します。UIDリスト機能で、自分のUIDを登録しておくと簡単に使えます。原神の設定でキャラ詳細を公開にすると、キャラステータスも確認できます。\
                ")
        elif select.values[0] == "UIDリストコマンド":
            print(
                f"help - UIDリストコマンド\n実行者:{interaction.user.name}\n鯖名:{interaction.guild.name}")
            embed.add_field(
                name=f"いちいち確認するのが面倒なUIDを管理するコマンドです。",
                value=f"\
                    \n**・/uidlist get**\n登録され、公開設定が「公開」になっているUIDがここに表示されます。\
                    \n**・/uidlist control**\n登録したUIDを管理するパネルを表示します。UIDの登録や削除、公開設定の切り替えもここからできます。\
                ")
        elif select.values[0] == "祈願コマンド":
            print(
                f"help - 祈願コマンド\n実行者:{interaction.user.name}\n鯖名:{interaction.guild.name}")
            embed.add_field(
                name=f"いわゆるガチャシミュレーターです。天井もユーザーごとにカウントされています。",
                value=f"\
                    \n**・/wish character**\n原神のガチャ排出時に表示されるイラストを検索します。\
                    \n**・/wish get**\n原神のガチャを引きます。\
                    "
            )
        elif select.values[0] == "便利コマンド":
            print(
                f"help - 便利コマンド\n実行者:{interaction.user.name}\n鯖名:{interaction.guild.name}")
            embed.add_field(
                name=f"botを活用する上で覚えておきたいコマンドたちです。",
                value=f"\
                    \n**・/genbot help**\n迷ったらこちらから確認しよう。\
                    \n**・/genbot today**\n今日の日替わり秘境（天賦本や武器突破素材）や、デイリー更新まであと何分？を表示！\
                    \n**・/genbot report**\nバグ・不具合報告はこちらからよろしくお願いいたします...\
                    \n**・/genbot event**\n原神のイベントを確認できます。\
                    \n**・/genbot code**\nワンボタンで原神報酬コードを使いたい方にどうぞっ！\
                ")
        elif select.values[0] == "聖遺物スコア計算コマンド":
            print(
                f"help - 聖遺物スコア計算コマンド\n実行者:{interaction.user.name}\n鯖名:{interaction.guild.name}")
            embed.add_field(
                name=f"聖遺物スコア計算を簡単にしてくれるコマンドです。",
                value=f"\
                    \n**・/artifact get**\n会心率基準で簡単に計算してくれます。数値はコマンド実行時に入力します。\
                    \n**・/artifact get_detail**\nHP基準や防御力基準など、より詳細に設定して計算します。\
                ")
        elif select.values[0] == "通知コマンド":
            print(
                f"help - 通知コマンド\n実行者:{interaction.user.name}\n鯖名:{interaction.guild.name}")
            embed.add_field(
                name=f"樹脂が溢れないように通知してくれるコマンドです。",
                value=f"\
                    \n**・/notification resin**\n現在の樹脂量を入力することで、溢れる前に通知します。\
                ")
        elif select.values[0] == "設定コマンド":
            print(
                f"help - 設定コマンド\n実行者:{interaction.user.name}\n鯖名:{interaction.guild.name}")
            embed.add_field(
                name=f"通知チャンネルなどを設定するコマンドです。",
                value=f"\
                    \n**・/setting channel**\n樹脂通知をするチャンネルを設定します。\
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

            channel = await main.sendChannel(1021082211618930801)
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
                    label="/genbot",
                    description="help、today等",),
            discord.SelectOption(
                label="/uidlist",
                description="get、controle等",),
            discord.SelectOption(
                label="/genshinstat",
                description="get等"),
            discord.SelectOption(
                label="/wish",
                description="get、get_n等"),
            discord.SelectOption(
                label="/setting",
                description="channel等"),
            discord.SelectOption(
                label="/artifact",
                description="get等"),
            discord.SelectOption(
                label="/notification",
                description="resin等"),
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
        data = mk.notes_create(text=self.text, reply_id=self.post_id)
        post_id = data["createdNote"]["id"]
        profile = mk.i()
        embed = discord.Embed(title=f"Replay @{self.post_user_name} by {profile['name']}", description='@'+profile['username']+'@'+user_data.instance)
        embed.set_thumbnail(url=profile['avatarUrl'])
        embed.add_field(name="投稿内容", value=self.text)
        view = ActionButtontView(post_id=post_id, post_user_name=profile['name'])
        await interaction.response.send_message(embed=embed, view=view, ephemeral=sql.Ephemeral.is_ephemeral(interaction.guild_id))

class RepostModal(discord.ui.Modal):
    def __init__(self, post_id, post_user_name):
        super().__init__(title="リポスト")
        self.post_id = post_id
        self.post_user_name = post_user_name

        self.text = discord.ui.InputText(
            label="リポストテキストを入力してね（必須ではありません）",
            style=discord.InputTextStyle.short,
        )
        self.add_item(self.text)

    async def callback(self, interaction: discord.Interaction) -> None:
        print(self.text)
        user_data = sql.User.get_user_list(user_id=interaction.user.id)
        user_data = user_data[0]
        mk = Misskey(user_data.instance, i=user_data.api_key)
        data = mk.notes_create(text=self.text, repost_id=self.post_id)
        post_id = data["createdNote"]["id"]
        profile = mk.i()
        embed = discord.Embed(title=f"Repost @{self.post_user_name} by {profile['name']}", description='@'+profile['username']+'@'+user_data.instance)
        embed.set_thumbnail(url=profile['avatarUrl'])
        if self.text:
            embed.add_field(name="投稿内容", value=self.text)
        view = ActionButtontView(post_id=post_id, post_user_name=profile['name'])
        await interaction.response.send_message(embed=embed, view=view, ephemeral=sql.Ephemeral.is_ephemeral(interaction.guild_id))

class ActionButtontView(View):
    def __init__(self, post_id, post_user_name):
        super().__init__()
        self.post_id = post_id
        self.post_user_name = post_user_name

    @discord.ui.button(emoji="↩")
    async def replay(self, _: discord.ui.Button, interaction: discord.Interaction):
        user_data = sql.User.get_user_list(user_id=interaction.user.id)
        if user_data == []:
            embed = discord.Embed(title=f"<@{interaction.user.id}> 事前にユーザーを登録してください。")
            await interaction.response.send_message(embed=embed, ephemeral=sql.Ephemeral.is_ephemeral(interaction.guild_id))
            return
        await interaction.response.send_modal(ReplayModal(post_id=self.post_id, post_user_name=self.post_user_name))
    
    @discord.ui.button(emoji="🔄")
    async def nextday(self, _: discord.ui.Button, interaction: discord.Interaction):
        user_data = sql.User.get_user_list(user_id=interaction.user.id)
        if user_data == []:
            embed = discord.Embed(title=f"<@{interaction.user.id}> 事前にユーザーを登録してください。")
            await interaction.response.send_message(embed=embed, ephemeral=sql.Ephemeral.is_ephemeral(interaction.guild_id))
            return
        await interaction.response.send_modal(RepostModal(post_id=self.post_id, post_user_name=self.post_user_name))

class MisskeyCog(commands.Cog):

    def __init__(self, bot):
        print('misskey_init')
        self.bot = bot

    misskey = SlashCommandGroup('misskey', 'test')

    @misskey.command(name='profile', description='プロフィール')
    async def code(
            self, 
            ctx: discord.ApplicationContext, 
            ):
        
        user_data = sql.User.get_user_list(user_id=ctx.author.id)
        if user_data == []:
            embed = discord.Embed(title=f"エラー・事前にユーザーを登録してください。")
            await ctx.respond(embed=embed, ephemeral=sql.Ephemeral.is_ephemeral(ctx.guild_id))

        user_data = user_data[0]
        mk = Misskey(user_data.instance)
        mk.token = user_data.api_key
        print(mk.i())
        profile = mk.i()
        embed = discord.Embed(title=f"{profile['name']} さんのプロフィール", description='@'+profile['username']+'@'+user_data.instance)
        print(profile['avatarUrl'])
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
        data = mk.notes_create(text=text, cw=is_content_warning, local_only=is_local_only)
        post_id = data["createdNote"]["id"]
        profile = mk.i()
        embed = discord.Embed(title=f"{profile['name']} さんのプロフィール", description='@'+profile['username']+'@'+user_data.instance)
        embed.set_thumbnail(url=profile['avatarUrl'])
        embed.add_field(name="投稿内容", value=text)
        view = ActionButtontView(post_id=post_id, post_user_name=profile['name'])
        await ctx.respond(embed=embed, view=view, ephemeral=sql.Ephemeral.is_ephemeral(ctx.guild_id))

def setup(bot):
    bot.add_cog(MisskeyCog(bot))
