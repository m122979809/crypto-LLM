import os
import configparser
from psycopg2 import pool

class PostgreSQL:
    """PostgreSQL 資料庫管理物件，支援連線池"""

    def __init__(self):
        """讀取設定，初始化連線池"""
        self.config = self.load_db_config()
        self.connection_pool = pool.SimpleConnectionPool(
            minconn=1,  # 最少連線數
            maxconn=10, # 最多連線數
            **self.config
        )

    def load_db_config(self):
        """讀取 config.ini 設定檔"""
        config = configparser.ConfigParser()
        config.read(os.path.join(os.path.dirname(__file__), "../config.ini"))
        return {
            "dbname": config["database"]["dbname"],
            "user": config["database"]["user"],
            "password": config["database"]["password"],
            "host": config["database"]["host"],
            "port": config["database"]["port"]
        }

    def get_connection(self):
        """從連線池取得一個連線"""
        return self.connection_pool.getconn()

    def release_connection(self, conn):
        """釋放連線回連線池"""
        self.connection_pool.putconn(conn)

    def query(self, sql, params=None, fetchall=True):
        """執行 SQL 查詢"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql, params or ())
                if fetchall:
                    return cursor.fetchall()  # 取得所有結果
                return cursor.fetchone()  # 取得一條結果
        finally:
            self.release_connection(conn)  # 釋放連線
    
    def put_connection(self, conn):
        self.connection_pool.putconn(conn)

# ✅ 初始化 PostgreSQL 物件
db = PostgreSQL()
