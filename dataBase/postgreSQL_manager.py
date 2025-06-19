import os
import pandas as pd
import hashlib
from decimal import Decimal, ROUND_HALF_UP
from dataBase.postgreSQL import db

# 創建表格

def create_tables():
    commands = [
        """
        CREATE EXTENSION IF NOT EXISTS "pgcrypto";
        
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            created_at TIMESTAMP DEFAULT NOW(),
            title TEXT -- optional, 可以給每次對話取名字
        );

        -- chat_messages
        CREATE TABLE IF NOT EXISTS chat_messages (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            session_id UUID REFERENCES chat_sessions(id) ON DELETE CASCADE,
            sender TEXT CHECK (sender IN ('user', 'bot')),
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS news (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            body TEXT NOT NULL,
            published_at TIMESTAMP,
            url TEXT,              
            keywords TEXT,      
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS crypto_prices (
            symbol VARCHAR(10) NOT NULL,
            id SERIAL NOT NULL,
            price DECIMAL(20,8) NOT NULL,
            volume DECIMAL(20,8),
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (symbol, id)
        ) PARTITION BY LIST (symbol);
        """,
        """
        CREATE TABLE IF NOT EXISTS crypto_prices_btc
        PARTITION OF crypto_prices FOR VALUES IN ('BTC');
        """,
        """
        CREATE TABLE IF NOT EXISTS crypto_prices_bnb
        PARTITION OF crypto_prices FOR VALUES IN ('BNB');
        """,
        """
        CREATE TABLE IF NOT EXISTS crypto_prices_ada
        PARTITION OF crypto_prices FOR VALUES IN ('ADA');
        """,
        """
        CREATE TABLE IF NOT EXISTS crypto_prices_doge
        PARTITION OF crypto_prices FOR VALUES IN ('DOGE');
        """,
        """
        CREATE TABLE IF NOT EXISTS crypto_prices_eth
        PARTITION OF crypto_prices FOR VALUES IN ('ETH');
        """,
        """
        CREATE TABLE IF NOT EXISTS crypto_prices_hbar
        PARTITION OF crypto_prices FOR VALUES IN ('HBAR');
        """,
        """
        CREATE TABLE IF NOT EXISTS crypto_prices_ltc
        PARTITION OF crypto_prices FOR VALUES IN ('LTC');
        """,
        """
        CREATE TABLE IF NOT EXISTS crypto_prices_sol
        PARTITION OF crypto_prices FOR VALUES IN ('SOL');
        """,
        """
        CREATE TABLE IF NOT EXISTS crypto_prices_trx
        PARTITION OF crypto_prices FOR VALUES IN ('TRX');
        """,
        """
        CREATE TABLE IF NOT EXISTS crypto_prices_xlm
        PARTITION OF crypto_prices FOR VALUES IN ('XLM');
        """,
        """
        CREATE TABLE IF NOT EXISTS crypto_prices_xrp
        PARTITION OF crypto_prices FOR VALUES IN ('XRP');
        """,
        # 指標主表與子表
        """
        CREATE TABLE IF NOT EXISTS crypto_indicators (
            symbol VARCHAR(10) NOT NULL,
            recorded_at TIMESTAMP NOT NULL,
            rsi_14 DECIMAL(10, 4),
            macd DECIMAL(20, 8),
            macd_signal DECIMAL(20, 8),
            bb_upper DECIMAL(20, 8),
            bb_middle DECIMAL(20, 8),
            bb_lower DECIMAL(20, 8),
            PRIMARY KEY (symbol, recorded_at)
        ) PARTITION BY LIST (symbol);
        """,
        """
        CREATE TABLE IF NOT EXISTS crypto_indicators_btc
        PARTITION OF crypto_indicators FOR VALUES IN ('BTC');
        """,
        """
        CREATE TABLE IF NOT EXISTS crypto_indicators_bnb
        PARTITION OF crypto_indicators FOR VALUES IN ('BNB');
        """,
        """
        CREATE TABLE IF NOT EXISTS crypto_indicators_ada
        PARTITION OF crypto_indicators FOR VALUES IN ('ADA');
        """,
        """
        CREATE TABLE IF NOT EXISTS crypto_indicators_doge
        PARTITION OF crypto_indicators FOR VALUES IN ('DOGE');
        """,
        """
        CREATE TABLE IF NOT EXISTS crypto_indicators_eth
        PARTITION OF crypto_indicators FOR VALUES IN ('ETH');
        """,
        """
        CREATE TABLE IF NOT EXISTS crypto_indicators_hbar
        PARTITION OF crypto_indicators FOR VALUES IN ('HBAR');
        """,
        """
        CREATE TABLE IF NOT EXISTS crypto_indicators_ltc
        PARTITION OF crypto_indicators FOR VALUES IN ('LTC');
        """,
        """
        CREATE TABLE IF NOT EXISTS crypto_indicators_sol
        PARTITION OF crypto_indicators FOR VALUES IN ('SOL');
        """,
        """
        CREATE TABLE IF NOT EXISTS crypto_indicators_trx
        PARTITION OF crypto_indicators FOR VALUES IN ('TRX');
        """,
        """
        CREATE TABLE IF NOT EXISTS crypto_indicators_xlm
        PARTITION OF crypto_indicators FOR VALUES IN ('XLM');
        """,
        """
        CREATE TABLE IF NOT EXISTS crypto_indicators_xrp
        PARTITION OF crypto_indicators FOR VALUES IN ('XRP');
        """
    ]

    conn = db.get_connection()
    cur = conn.cursor()
    for command in commands:
        cur.execute(command)
    conn.commit()
    cur.close()
    conn.close()
    print("資料表確認完成（若不存在則已建立）")

# 更新 `news` 表格
def update_news_table():
    conn = db.get_connection()
    cur = conn.cursor()

    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'news' AND column_name = 'url';")
    if not cur.fetchone():
        cur.execute("ALTER TABLE news ADD COLUMN url TEXT;")
        print("✅ 已新增 `url` 欄位")

    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'news' AND column_name = 'keywords';")
    if not cur.fetchone():
        cur.execute("ALTER TABLE news ADD COLUMN keywords TEXT;")
        print("✅ 已新增 `keywords` 欄位")

    conn.commit()
    cur.close()
    conn.close()
    print("✅ `news` 表格更新完成")

# 插入新聞資料
def insert_news():
    news_file = os.path.join(os.path.dirname(__file__), "../news/coindesk_news.csv")
    df = pd.read_csv(news_file, header=0, names=["timestamp", "published_at", "title", "body", "url", "keywords"], skiprows=1)
    df["published_at"] = pd.to_datetime(df["published_at"], errors="coerce")
    df = df.dropna(subset=["published_at", "title", "body"])  # ✅ 確保 title 和 body 都不為 NaN

    conn = db.get_connection()
    cur = conn.cursor()

    cur.execute("SELECT MAX(published_at) FROM news;")
    last_news_date = cur.fetchone()[0]

    if last_news_date is not None:
        df = df[df["published_at"] > last_news_date]

    if df.empty:
        print("✅ 沒有新的新聞需要插入")
    else:
        for _, row in df.iterrows():
            # 強制轉為字串，避免 TypeError
            title = str(row["title"])
            body = str(row["body"])

            doc_id = hashlib.md5((title + body).encode()).hexdigest()
            cur.execute("""
                INSERT INTO news (id, title, body, published_at, url, keywords)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE 
                SET url = EXCLUDED.url, 
                    keywords = EXCLUDED.keywords;
            """, (
                doc_id,
                title,
                body,
                row["published_at"],
                row["url"] if "url" in row and pd.notna(row["url"]) else None,
                row["keywords"] if "keywords" in row and pd.notna(row["keywords"]) else None
            ))

        conn.commit()
        print(f"✅ 已插入或更新 {len(df)} 則新聞")

    cur.close()
    conn.close()

def round_decimal(value, places=8):
    return Decimal(value).quantize(Decimal(f'1.{"0" * places}'), rounding=ROUND_HALF_UP)

def insert_crypto_prices():
    crypto_symbols = ["ADA", "BNB", "BTC", "DOGE", "ETH", "HBAR", "LTC", "SOL", "TRX", "XLM", "XRP"]
    base_path = os.path.join(os.path.dirname(__file__), "../price")

    conn = db.get_connection()
    cur = conn.cursor()

    for symbol in crypto_symbols:
        file_path = os.path.join(base_path, f"{symbol}USDT_historical_prices.csv")
        if not os.path.exists(file_path):
            print(f"⚠️ 找不到檔案: {file_path}")
            continue

        df = pd.read_csv(file_path)
        df["Date"] = pd.to_datetime(df["Date"])

        cur.execute("SELECT MAX(recorded_at) FROM crypto_prices WHERE symbol = %s;", (symbol,))
        last_price_date = cur.fetchone()[0]

        if last_price_date is not None:
            df = df[df["Date"] > last_price_date]

        if df.empty:
            print(f"✅ {symbol} 沒有新的幣價需要插入")
            continue

        for _, row in df.iterrows():
            cur.execute("""
                INSERT INTO crypto_prices (symbol, price, volume, recorded_at)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT DO NOTHING;
            """, (
                symbol,
                round_decimal(row["Close"]),
                round_decimal(row["Volume"]) if row["Volume"] else None,
                row["Date"]
            ))

        conn.commit()
        print(f"✅ {symbol} 已插入 {len(df)} 筆新數據")

    cur.close()
    conn.close()

if __name__ == "__main__":
    create_tables()
    insert_news()
    insert_crypto_prices()
