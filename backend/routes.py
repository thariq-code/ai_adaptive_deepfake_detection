from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.auth import create_user, authenticate_user, generate_token
from backend.detection import detect, history, dashboard

def register_routes(app):
    @app.route("/api/register", methods=["POST"])
    def register():
        data = request.get_json()
        email = data.get("email")
        password = data.get("password")
        if not email or not password:
            return jsonify({"error": "Email and password required"}), 400
        user_id = create_user(email, password)
        if not user_id:
            return jsonify({"error": "User already exists"}), 409
        token = generate_token(user_id)
        return jsonify({"access_token": token}), 201

    @app.route("/api/login", methods=["POST"])
    def login():
        data = request.get_json()
        email = data.get("email")
        password = data.get("password")
        if not email or not password:
            return jsonify({"error": "Email and password required"}), 400
        user_id = authenticate_user(email, password)
        if not user_id:
            return jsonify({"error": "Invalid credentials"}), 401
        token = generate_token(user_id)
        return jsonify({"access_token": token}), 200

    @app.route("/api/detect", methods=["POST"])
    @jwt_required()
    def detect_route():
        return detect()

    @app.route("/api/history", methods=["GET"])
    @jwt_required()
    def history_route():
        return history()

    @app.route("/api/dashboard", methods=["GET"])
    @jwt_required()
    def dashboard_route():
        return dashboard()