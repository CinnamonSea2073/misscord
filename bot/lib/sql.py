from datetime import datetime
from typing import Tuple
import os
import psycopg2
import discord


# 予め定数として接続先を定義しておきます
print(os.getenv('SQL'))


class database:
    __DSN = 'postgresql://{user}:{password}@{host}:{port}/{dbname}'.format(
        user=os.getenv('POSTGRES_USER'),  # ユーザ
        password=os.getenv('POSTGRES_PASSWORD'),  # パスワード
        host=os.getenv('HOST'),  # ホスト名
        port=os.getenv('PORT'),  # ポート
        dbname=os.getenv('POSTGRES_DB'))  # データベース名

    def __connection():
        return psycopg2.connect(database.__DSN)

    def load_sql(sql: str, data: Tuple[int, str, datetime] = (), default: any = dict()) -> any:
        """
        sqlを読み込んでそのままDictとかListにします。
        読み込めなかった場合にはdefaultの値を返します。
        → おそらく使う用途ない気がする
        """
        try:
            return database.load_data_sql(sql, data)
        except:
            return default

    def load_data_sql(sql: str, data: Tuple) -> Tuple[Tuple[int, str, datetime]]:
        """
        sqlを読み込んでTuple型で返却します。
        この時、返却値はtable構造に依存します。
        SQL構文などに問題がある場合は、それに基づくErrorをthrowします。
        """
        connector = database.__connection()

        cursor = connector.cursor()
        cursor.execute(sql, data)
        result = cursor.fetchall()
        cursor.close()
        connector.close()
        return result

    def table_update_sql(sql: str, data: Tuple[int, str, datetime] = ()) -> None:
        """
        sqlを実行しtableの更新を行うための関数です。
        SQL構文などに問題がある場合は、それに基づくErrorをthrowします。
        """
        try:
            connector = database.__connection()
            cursor = connector.cursor()
            cursor.execute(sql, data)
        finally:
            connector.commit()
            cursor.close()
            connector.close()


class Guild:
    def __init__(self, id: int):
        self.id = id

    def set_guilds(guild_id_list: list[discord.Guild]):
        """
        guildオブジェクトの配列を受け取り登録を行います。
        """
        if len(guild_id_list) > 0:
            database.table_update_sql(
                sql="insert into bot_table values " +
                    ",".join(["(%s)"] * len(guild_id_list)) +
                    " ON CONFLICT DO NOTHING",
                data=[v.id for v in guild_id_list],
            )

    def get_count():
        """
        guildの数を取得し返します。
        """
        result = database.load_data_sql(
            sql="select count(*) from bot_table", data=None)
        return result[0][0]


class User:
    def __init__(self, user_id: int, api_key: int, instance: str, user_name:str):
        self.user_id = user_id
        self.api_key = api_key
        self.instance = instance
        self.user_name = user_name

    def get_user_list(user_id: int):
        """
        user_idからユーザーが登録したUIDの一覧を取得します
        """
        # print(user_id)
        data = database.load_data_sql(
            sql="""
            select user_id, api_key, instance_address, user_name from user_table where user_id = %s
            """,
            data=(user_id, )
        )
        # print(data)
        return [User(v[0], v[1], v[2], v[3]) for v in data]

    def insert_user(user):
        """
        利用者情報を新規で追加します。
        この時Userオブジェクトは全ての値が保持されている必要があります。
        """
        # 一意制約違反に引っかかる場合がある気がするのでtry exceptしてます
        try:
            database.table_update_sql(
                sql="""
                insert into user_table values(%s, %s, %s, %s) 
                """,
                data=(user.user_id, user.api_key, user.instance, user.user_name)
            )
            return user
        except:
            User.update_user(user)

    def update_user(user):
        """
        利用者情報を更新する場合に利用します。
        この時Userオブジェクトは全ての値が保持されている必要があります。
        """
        database.table_update_sql(
            sql="""
            update user_table set api_key=%s where user_id = %s and instance_address = %s
            """,
            data=(user.api_key, user.user_id, user.instance, )
        )

    def delete_user(user_id: int, api_key: int):
        """
        利用者情報を削除する場合に利用します。
        """
        database.table_update_sql(
            sql="""
            delete from user_table where user_id = %s and api_key = %s
            """,
            data=(user_id, api_key)
        )


class Ephemeral:
    def __init__(self, guild_id: int, ephemeral: bool):
        self.guild_id = guild_id
        self.ephemeral = ephemeral

    def set_ephemeral(guild_id: int, ephemeral: bool):
        """
        Ephemeralを指定したboolにする処理です。
        """
        database.table_update_sql(
            sql="""
            update public_server_config 
            set is_ephemeral = %s
            where serverid = %s
            """,
            data=(ephemeral, guild_id))
        
    def init_ephemeral(guild_id: int):
        """
        guild_idのデータを初期化します。
        """
        database.table_update_sql(
            sql="""
            insert into public_server_config(serverid)
            values(%s)
            """,
            data=(guild_id,),
        )

    def is_ephemeral(guild_id: int):
        """
        そのサーバーでephemeralが有効かどうか取得する関数です。
        各コマンドのephemeral制御のために利用します。
        """
        try:
            result = database.load_data_sql(
                sql="""
                select is_ephemeral
                from public_server_config
                where serverid = %s
                """,
                data=(guild_id,))
            return result[0][0]
        except:
            database.table_update_sql(
                sql="""
                insert into public_server_config(serverid)
                values(%s)
                """,
                data=(guild_id,),
            )
            return False

class channel:
    def __init__(self, guilt_id: int, channel_id: int):
        self.guilt_id = guilt_id
        self.channel_id = channel_id

    def get_channel(guild_id):
        # sqlでデータとってくるやつ
        print(guild_id)
        result = database.load_data_sql(execute="""
        select *
        from server_table
        where serverid = %s""", data=(guild_id,))
        print(result)
        data: list[channel] = [
            channel(guilt_id=v[0], channel_id=v[1])
            for v in result
        ]
        return data
