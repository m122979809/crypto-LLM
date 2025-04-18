from flask import Flask
from controllers.deepseek_controller import deepseek_bp

app = Flask(__name__)

# 註冊 Blueprint
app.register_blueprint(deepseek_bp, url_prefix="/api")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
