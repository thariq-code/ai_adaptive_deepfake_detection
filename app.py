import os
from flask import Flask, render_template
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from backend.routes import register_routes
from database.mongo import init_db
from config import Config

app = Flask(__name__, template_folder="frontend/templates", static_folder="frontend/static")
app.config.from_object(Config)

CORS(app)
jwt = JWTManager(app)

init_db(app)

register_routes(app)

@app.route("/")
def index():
    return render_template("login.html")

@app.route("/login")
def login_page():
    return render_template("login.html")

@app.route("/register")
def register_page():
    return render_template("register.html")

@app.route("/dashboard")
def dashboard_page():
    return render_template("dashboard.html")

@app.route("/history")
def history_page():
    return render_template("history.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)