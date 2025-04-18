import requests
import datetime
import csv
import os
import pytz
from dataBase.save_news import process_and_store_news,read_news_from_csv
from dataBase.postgreSQL_manager import insert_news

# API URL，增加 limit 參數
API_URL = "https://data-api.coindesk.com/news/v1/article/list?lang=EN&limit=100"

# 確保 news 目錄存在
news_dir = "news"
os.makedirs(news_dir, exist_ok=True)

# 檔案路徑
filename = os.path.join(news_dir, "coindesk_news.csv")

# 台灣時區
taiwan_tz = pytz.timezone('Asia/Taipei')

def fetch_and_save_news_to_csv():
    response = requests.get(API_URL)

    if response.status_code == 200:
        data = response.json()

        with open(filename, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            
            writer.writerow(["Timestamp", "Published Time", "Title", "Body", "URL", "Keywords"])

            for article in data["Data"]:
                timestamp = article["PUBLISHED_ON"]  # 原始 Unix 時間戳（秒）

                # 轉換為 UTC 時間
                utc_time = datetime.datetime.utcfromtimestamp(timestamp).replace(tzinfo=pytz.utc)
                
                # 轉換為台灣時間
                taiwan_time = utc_time.astimezone(taiwan_tz)
                
                # 格式化為可讀格式
                published_time = taiwan_time.strftime('%Y-%m-%d %H:%M:%S')
                title = article["TITLE"]
                body = article["BODY"]
                url = article["URL"]  # 新增文章 URL

                # 🔍 取得關鍵字（有些文章可能沒有 KEYWORDS）
                keywords = article.get("KEYWORDS", "N/A")
                if isinstance(keywords, str):
                    keywords = keywords.replace(",", "|")  # 確保格式統一
                else:
                    keywords = "N/A"

                # ✨ 存入 CSV
                writer.writerow([timestamp, published_time, title, body, url, keywords])
        
        insert_news()
        news_data = read_news_from_csv()
        if news_data:
            process_and_store_news(news_data)

        print(f"✅ Data has been saved to {filename}")
    else:
        print(f"❌ Failed to retrieve data. HTTP Status code: {response.status_code}")

if __name__ == '__main__':
    fetch_and_save_news_to_csv()