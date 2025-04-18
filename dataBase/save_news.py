import os
import csv
import time
from dataBase.news_operation import *

# CSV 檔案路徑
CSV_FILE = os.path.join("news", "coindesk_news.csv")

# 讀取新聞資料，並在讀取時去重
def read_news_from_csv():
    news_data = []
    seen_titles = set()  # 用來記錄已經讀過的標題，避免重複
    
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode="r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                title = row["Title"]
                body = row["Body"]
                published_time_str = row["Published Time"]

                # 避免標題重複
                if title not in seen_titles:
                    seen_titles.add(title)

                    # 解析時間（格式：2024-03-02 17:20:00）
                    published_time_struct = time.strptime(published_time_str, "%Y-%m-%d %H:%M:%S")

                    news_data.append({
                        "TITLE": title,
                        "BODY": body,
                        "PUBLISHED_TIME": published_time_struct
                    })
    else:
        print(f"❌ No CSV file found at {CSV_FILE}")

    return news_data

# 將新聞存入向量資料庫
def process_and_store_news(news_data):
    new_count = 0

    for article in news_data:
        title = article["TITLE"]
        body = article["BODY"]
        published_time = article["PUBLISHED_TIME"]

        create_news(title, body, published_time)
        new_count += 1

    print(f"✅ 新增 {new_count} 則新聞至向量資料庫。" if new_count else "沒有新的新聞可存入。")

# 測試查找功能
def test_query():
    while True:
        print("\n🔍 選擇查找方式：")
        print("[1] 透過關鍵字查找")
        print("[2] 透過新聞 ID 查找")
        print("[Enter] 結束查找")
        
        choice = input("請選擇查找方式：").strip()

        if choice == "1":
            query_text = input("\n🔎 輸入查找關鍵字：").strip()
            if not query_text:
                continue
            
            results = read_news(query_text=query_text, top_k=5)
            if results:
                print("\n🔎 查詢結果：")
                for i, news in enumerate(results):  
                    print(f"\n[{i+1}] {news[0]}")  
                    print(f"📰 {news[1][:200]}...") 
            else:
                print("⚠️ 沒有找到相關新聞！")
        
        elif choice == "2":
            news_id = input("\n🆔 輸入新聞 ID：").strip()
            if not news_id:
                continue
            
            result = read_news(news_id=news_id)
            if result and "documents" in result and result["documents"]:
                news = result["documents"][0]
                print(f"\n📄 新聞標題：{news[0]}")  # ✅ 修正
                print(f"📰 內容：{news[1]}")  # ✅ 修正
            else:
                print("⚠️ 找不到此新聞！")
        
        elif choice == "":
            print("🚪 結束查找測試")
            break
        else:
            print("⚠️ 輸入無效，請重新選擇！")

# 主程式
if __name__ == '__main__':
    news_data = read_news_from_csv()
    if news_data:
        process_and_store_news(news_data)

    # 查找測試
    # test_query()
