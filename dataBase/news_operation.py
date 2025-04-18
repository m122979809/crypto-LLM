import hashlib
import time
from datetime import datetime
from sentence_transformers import SentenceTransformer
from dataBase.chromaDB import chroma_db
from dataBase.postgreSQL import db

# 初始化 SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')

def is_title_exists(title):
    """檢查新聞標題是否已存在於資料庫"""
    conn = chroma_db.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM news WHERE title = %s;", (title,))
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return count > 0


# 產生文本的向量嵌入
def create_embeddings(texts):
    return model.encode(texts).tolist()

# 創建（Create）新聞
def create_news(title, body, published_time):
    doc_id = hashlib.md5((title + body).encode()).hexdigest()  # 產生唯一 ID
    content = f"{title}\n{body}"
    embedding = create_embeddings([content])[0]  # 轉換為向量

    # 轉換成標準格式
    if isinstance(published_time, time.struct_time):
        published_time_str = time.strftime("%Y-%m-%d %H:%M:%S", published_time)
        timestamp = time.mktime(published_time)
    elif isinstance(published_time, datetime):
        published_time_str = published_time.strftime("%Y-%m-%d %H:%M:%S")
        timestamp = published_time.timestamp()
    else:
        raise ValueError("❌ Unsupported time format")

    # 新增到向量資料庫
    chroma_db.add_document(
        doc_id,
        content,
        embedding,
        {
            "title": title,
            "published_time": published_time_str,
            "timestamp": timestamp
        }
    )
    print(f"✅ 新聞已儲存: {title} - {published_time_str}")

# 讀取（Read）新聞
def read_news(query_text=None, news_id=None, top_k=5):
    if news_id:  # 透過 ID 查找
        result = chroma_db.get_document_by_id(news_id)  # 查找指定 ID 的新聞
        if not result:
            return "❌ 找不到此新聞"
        
        # 如果找到新聞，返回 ID、標題、內容等信息
        return [{
            "id": news_id,
            "title": result[0].get("title", "無標題"),
            "content": result[0].get("content", "無內容"),
            "published_time": result[0].get("published_time", "未知時間")
        }]
    
    if query_text:  # 透過語意搜尋
        print(query_text + " searching...")
        embedding = create_embeddings([query_text])[0]  # 創建查詢的 embedding
        results = chroma_db.query_documents(query_embedding=[embedding], top_k=top_k)  # 查詢相關的新聞
        
        if not results["documents"]:
            return "⚠️ 沒有找到相關新聞"
        
        # 根據提供的資料結構，處理每篇新聞
        news_with_ids = []
        for doc, metadata, score, doc_id in zip(results["documents"][0], results["metadatas"][0], results["distances"][0], results["ids"][0]):
            news_with_ids.append({
                "id": doc_id,  # 使用查詢返回的 ID
                "title": metadata.get("title", "無標題"),
                "content": doc,  # 內容為查詢返回的文檔內容
                "published_time": metadata.get("published_time", "未知時間"),
                "score": score  # 返回相似度分數
            })
        
        return news_with_ids
    
    return "⚠️ 請提供查詢條件（新聞 ID 或 搜尋關鍵字）"

# 透過使用者輸入進行語意搜尋
def search_by_user_input():
    while True:
        user_input = input("\n🔍 輸入新聞關鍵字（輸入 'exit' 退出）：")
        if user_input.lower() == "exit":
            break
        results = read_news(query_text=user_input, top_k=5)
        
        # 確認結果是列表類型
        if isinstance(results, list):
            print("\n📌 相關新聞：")
            for idx, doc in enumerate(results, 1):
                # 只顯示 'title' 和 'id'
                print(f"{idx}. ID: {doc['id']}, Title: {doc['title']}")
        else:
            print(results)  # 顯示錯誤或提醒訊息

def clear_chroma_db():
    all_docs = chroma_db.collection.get(include=["metadatas"])
    for doc_id in all_docs["ids"]:
        chroma_db.delete_news(doc_id)
    print(f"🧹 已清空向量資料庫，共 {len(all_docs['ids'])} 筆")

def rebuild_chroma_from_postgres():
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT title, body, published_at FROM news;")  # 不再用 id，讓 create_news 自動產生
    rows = cur.fetchall()

    for title, body, published_at in rows:
        create_news(title, body, published_at)  # 由 create_news 處理向量、doc_id、metadata 建立

    cur.close()
    db.release_connection(conn)
    print(f"✅ 已將 {len(rows)} 筆資料重新建立到向量資料庫")

# 測試用
if __name__ == "__main__":
    # create_news("Bitcoin Price Surge", "Bitcoin price has increased by 5% today.", time.gmtime(1709400000))
    # search_by_user_input()
    clear_chroma_db()
    rebuild_chroma_from_postgres()    