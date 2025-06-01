from flask import Blueprint, request, jsonify
import models.chat_model as chat
from flask_cors import CORS

chat_bp = Blueprint("chat", __name__)
CORS(chat_bp, resources={r"/*": {"origins": "http://localhost:5173"}})

@chat_bp.route("/session", methods=["POST"])
def create_session():
    title = chat.generate_default_title()
    session_id = chat.create_session(title)
    return jsonify({"session_id": session_id, "title": title}), 201


@chat_bp.route("/message", methods=["POST"])
def save_message():
    data = request.get_json()
    session_id = data.get("session_id")
    sender = data.get("sender")  # 'user' or 'bot'
    message = data.get("message")

    if not all([session_id, sender, message]):
        return jsonify({"error": "Missing fields"}), 400

    chat.insert_message(session_id, sender, message)
    return jsonify({"status": "saved"}), 200

@chat_bp.route("/session/<session_id>", methods=["GET"])
def get_messages(session_id):
    messages = chat.get_session_messages(session_id)
    return jsonify([
        {"sender": m[0], "message": m[1], "created_at": m[2].isoformat()}
        for m in messages
    ])

@chat_bp.route("/sessions", methods=["GET"])
def get_all_sessions():
    sessions = chat.get_all_sessions()
    return jsonify([
        {"id": s[0], "title": s[1], "created_at": s[2].isoformat()}
        for s in sessions
    ])

@chat_bp.route("/session/<session_id>", methods=["PUT"])
def update_session_title(session_id):
    data = request.get_json()
    new_title = data.get("title")

    if not new_title:
        return jsonify({"error": "Missing title"}), 400

    chat.update_session_title(session_id, new_title)
    return jsonify({"status": "updated"}), 200

@chat_bp.route("/session/<session_id>", methods=["DELETE"])
def delete_session(session_id):
    chat.delete_session(session_id)
    return jsonify({"status": "deleted"}), 200


