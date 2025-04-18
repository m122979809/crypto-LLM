import pandas as pd
import os
from decimal import Decimal
from dataBase.postgreSQL import db

def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values("Date")
    close = df["Close"]

    # RSI (14)
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df["rsi_14"] = 100 - (100 / (1 + rs))

    # MACD
    ema_12 = close.ewm(span=12, adjust=False).mean()
    ema_26 = close.ewm(span=26, adjust=False).mean()
    df["macd"] = ema_12 - ema_26
    df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()

    # Bollinger Bands (20日均線 ± 2 std)
    ma_20 = close.rolling(window=20).mean()
    std_20 = close.rolling(window=20).std()
    df["bb_middle"] = ma_20
    df["bb_upper"] = ma_20 + (2 * std_20)
    df["bb_lower"] = ma_20 - (2 * std_20)

    return df[["Date", "rsi_14", "macd", "macd_signal", "bb_upper", "bb_middle", "bb_lower"]]

def round_decimal(value, places=8):
    return Decimal(value).quantize(Decimal(f'1.{"0" * places}')) if pd.notna(value) else None

def insert_indicators(symbol: str, indicators_df: pd.DataFrame):
    conn = db.get_connection()
    cur = conn.cursor()

    try:
        # 資料過濾
        cur.execute("SELECT MAX(recorded_at) FROM crypto_indicators WHERE symbol = %s;", (symbol,))
        last_date = cur.fetchone()[0]

        if last_date is not None:
            indicators_df = indicators_df[indicators_df["Date"] > last_date]

        if indicators_df.empty:
            print(f"✅ {symbol} 沒有新的指標需要插入")
            return

        # 寫入資料
        for _, row in indicators_df.iterrows():
            cur.execute("""
                INSERT INTO crypto_indicators (
                    symbol, recorded_at, 
                    rsi_14, macd, macd_signal, 
                    bb_upper, bb_middle, bb_lower
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING;
            """, (
                symbol,
                row["Date"],
                round_decimal(row["rsi_14"], 4),
                round_decimal(row["macd"]),
                round_decimal(row["macd_signal"]),
                round_decimal(row["bb_upper"]),
                round_decimal(row["bb_middle"]),
                round_decimal(row["bb_lower"]),
            ))

        conn.commit()
        print(f"✅ {symbol} 指標已插入 {len(indicators_df)} 筆")

    finally:
        # 不管有沒有錯，都確保釋放資源
        cur.close()
        db.put_connection(conn)

def calculate_and_insert_all_indicators():
    symbols = ["ADA", "BNB", "BTC", "DOGE", "ETH", "HBAR", "LTC", "SOL", "TRX", "XLM", "XRP"]
    base_path = os.path.join(os.path.dirname(__file__), "../price")

    for symbol in symbols:
        file_path = os.path.join(base_path, f"{symbol}USDT_historical_prices.csv")
        if not os.path.exists(file_path):
            print(f"❌ 找不到檔案: {file_path}")
            continue

        df = pd.read_csv(file_path)
        df["Date"] = pd.to_datetime(df["Date"])
        indicators_df = calculate_indicators(df)
        insert_indicators(symbol, indicators_df)

if __name__ == "__main__":
    calculate_and_insert_all_indicators()