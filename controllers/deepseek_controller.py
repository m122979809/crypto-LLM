from flask import Blueprint, request, jsonify
from models.deepseek_model import query_rag

# 建立 Flask Blueprint
deepseek_bp = Blueprint("deepseek", __name__)

@deepseek_bp.route("/generate", methods=["POST"])
def generate_response():
    """
    📌 DeepSeek RAG API
    這個 API 接收使用者的問題，並透過 DeepSeek 生成回答。
    
    Request Body:
    {
        "question": "比特幣價格趨勢？"
    }

    Response:
    {
        "answer": "根據最新新聞，比特幣價格..."
    }
    """
    data = request.get_json()
    question = data.get("question", "")

    if not question:
        return jsonify({"error": "請提供問題"}), 400

    try:
        answer = query_rag(question)
        return jsonify({"answer": answer})
    except Exception as e:
        return jsonify({"error": f"伺服器錯誤: {str(e)}"}), 500
