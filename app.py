from flask import Flask
from controllers.deepseek_controller import deepseek_bp
from flask_cors import CORS
from controllers.chat import chat_bp  # 加入聊天 Blueprint

app = Flask(__name__)
CORS(app)

# 註冊 Blueprint
app.register_blueprint(deepseek_bp, url_prefix="/api")
app.register_blueprint(chat_bp, url_prefix="/api/chat")  # 加上聊天 API

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
