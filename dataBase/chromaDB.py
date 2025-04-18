import chromadb
from datetime import datetime
from dataBase.postgreSQL import db  # 使用你提供的 PostgreSQL 封裝

class ChromaDB:
    """ChromaDB 資料庫管理物件"""

    def __init__(self, db_path="./chroma_db", collection_name="coindesk_news"):
        """初始化 ChromaDB 連線，並取得指定的 collection"""
        self.client = chromadb.PersistentClient(path=db_path)  # 初始化 client
        self.collection = self.client.get_or_create_collection(collection_name)  # 取得或創建 collection

    def add_document(self, doc_id, content, embedding, metadata):
        """新增文件到 ChromaDB"""
        self.collection.add(
            ids=[doc_id],
            documents=[content],
            embeddings=[embedding],
            metadatas=[metadata]
        )
        print(f"✅ 文件 {doc_id} 已新增至 ChromaDB")

    def query_documents(self, query_embedding, top_k=5, where=None):
        """根據查詢的嵌入向量來搜尋相關文件，可選擇加入 metadata 篩選條件"""
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=top_k,
            where=where  #加入 metadata 過濾條件
        )
        # print(results)
        return results

    def get_document_by_id(self, doc_id):
        """根據 ID 查詢文件"""
        result = self.collection.get(ids=[doc_id])
        return result if result else "❌ 找不到此文件"
    
    def delete_news(self,news_id):
        self.collection.delete(ids=[news_id])
        print(f"🗑️ 新聞已刪除: {news_id}")

chroma_db = ChromaDB(db_path="../chroma_db")

if __name__ == "__main__":
    chroma_db = ChromaDB(db_path="../chroma_db")
else:
    chroma_db = ChromaDB()