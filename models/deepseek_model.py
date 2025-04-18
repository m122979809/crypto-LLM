import requests
import configparser
import os
import json
from datetime import datetime, timedelta
from dataBase.chromaDB import ChromaDB
from dataBase.postgreSQL import db
import pandas as pd

config = configparser.ConfigParser()
config.read(os.path.abspath(os.path.join(os.path.dirname(__file__), "../config.ini")))
hf_api_key = config["API"]["huggingface_api_key"]

API_URL = "https://router.huggingface.co/novita/v3/openai/chat/completions"
headers = {"Authorization": f"Bearer {hf_api_key}"}

coin_translation = {
    "比特幣": "BTC",
    "以太幣": "ETH",
    "以太坊": "ETH",
    "狗狗幣": "DOGE",
    "柴犬幣": "SHIB",
    "幣安幣": "BNB",
    "瑞波幣": "XRP",
    "索拉納": "SOL",
    "波卡": "DOT",
    "萊特幣": "LTC",
}

def translate_to_english_symbols(text):
    for zh, symbol in coin_translation.items():
        text = text.replace(zh, symbol)
    return text

def extract_related_coins(user_query):
    user_query_translated = translate_to_english_symbols(user_query)

    prompt = f"""
你是一個幫助使用者分析加密貨幣的助手，請根據用戶問題，判斷他關心的幣種。

規則：
1. 若問題是「BTC適合買進嗎？」→ 回傳 ["BTC"]
2. 若問題是「除了BTC，還有什麼幣值得關注？」→ 回傳除了 BTC 以外的熱門幣（如 ["ETH", "SOL"]）
3. 若沒有提到特定幣種，就回傳目前熱門幣種（如 ["BTC", "ETH"]）

請用 JSON 陣列格式回傳幣種代號，不用任何解釋。

用戶問題：
"{user_query_translated}"
"""

    payload = {
        "model": "deepseek/deepseek-v3-0324",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 100
    }

    response = requests.post(API_URL, headers=headers, json=payload)
    if response.status_code != 200:
        print("無法擷取幣種，預設使用 BTC")
        return ["BTC"]
    try:
        result = json.loads(response.json()["choices"][0]["message"]["content"].strip())
        if isinstance(result, list):
            return result
        return ["BTC"]
    except:
        return ["BTC"]

def query_rag(question, top_k=5):
    chroma_db = ChromaDB()
    embeddings = create_embeddings([question])
    if not embeddings:
        return "❌ 無法生成問題的嵌入向量，請確認問題格式"

    coin_symbols = extract_related_coins(question)
    coin_names = ", ".join(coin_symbols)

    now = datetime.now()
    time_filter = now - timedelta(days=3)
    time_filter = time_filter.timestamp()

    try:
        news_results = chroma_db.query_documents(
            query_embedding=embeddings[0],
            top_k=top_k,
            where={"timestamp": {"$gte": time_filter}}
        )
    except Exception as e:
        return f"查詢 ChromaDB 時出錯：{str(e)}"

    if not news_results["documents"]:
        return "找不到相關新聞，請換個問題試試！"

    sorted_results = sorted(
        zip(news_results["documents"][0], news_results["metadatas"][0], news_results["distances"][0], news_results["ids"][0]),
        key=lambda x: x[1].get("timestamp", "1970-01-01"),
        reverse=True
    )

    news_sources = []
    conn = db.get_connection()
    cur = conn.cursor()

    for doc, metadata, score, doc_id in sorted_results:
        news_id, title = doc_id, metadata.get("title", "無標題")
        cur.execute("SELECT url FROM news WHERE id = %s;", (news_id,))
        result = cur.fetchone()
        url = result[0] if result else "無連結"
        news_sources.append(f"{title} : {url}")

    # 擷取幣種指標資料
    indicator_text = []
    for symbol in coin_symbols:
        cur.execute("""
            SELECT recorded_at, rsi_14, macd, macd_signal, bb_upper, bb_middle, bb_lower
            FROM crypto_indicators
            WHERE symbol = %s
            ORDER BY recorded_at DESC
            LIMIT 1;
        """, (symbol,))
        indicator = cur.fetchone()
        if indicator:
            date, rsi, macd, macd_sig, bb_up, bb_mid, bb_low = indicator
            indicator_text.append(
                f"{symbol}（{date.date()}）：RSI={rsi}, MACD={macd}, Signal={macd_sig}, BB(上/中/下)={bb_up}/{bb_mid}/{bb_low}"
            )

    cur.close()
    db.put_connection(conn)

    indicators_str = "\n".join(indicator_text)
    context = "\n".join(news_sources)
    messages = [
        {"role": "system", "content": "你是一個根據最新新聞與技術指標幫助使用者分析幣價的 AI 助手。"},
        {"role": "user", "content": f"根據以下新聞與幣種技術指標資料回答問題（幣種：{coin_names}）：\n\n[新聞]\n{context}\n\n[技術指標]\n{indicators_str}\n\n問題：{question}"},
    ]

    payload = {
        "model": "deepseek/deepseek-v3-0324",
        "messages": messages,
        "max_tokens": 500
    }

    response = requests.post(API_URL, headers=headers, json=payload)
    if response.status_code != 200:
        return f"❌ API 錯誤: {response.json()}"

    answer = response.json()["choices"][0]["message"]["content"].strip()
    return {
        "answer": answer,
        "indicators": indicator_text,
        "news": news_sources
    }

def create_embeddings(texts):
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('all-MiniLM-L6-v2')
    try:
        embeddings = model.encode(texts)
        return embeddings.tolist()
    except Exception as e:
        print(f"❌ 嵌入向量生成錯誤: {str(e)}")
        return None

if __name__ == "__main__":
    while True:
        user_input = input("\n❓ 輸入你的問題（輸入 'exit' 退出）：")
        if user_input.lower() == "exit":
            break
        result = query_rag(user_input)
        if isinstance(result, dict):
            print("\n" + result["answer"])
            print("\n📈 技術指標：")
            for ind in result["indicators"]:
                print("- " + ind)
            print("\n🔗 相關新聞來源：")
            for news in result["news"]:
                print("- " + news)
        else:
            print("\n" + result)