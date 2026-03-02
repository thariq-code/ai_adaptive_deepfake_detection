from pymongo import MongoClient
from flask import current_app


def init_db(app):
    with app.app_context():
        mongo_uri = app.config.get("MONGO_URI")

        try:
            client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
            client.admin.command("ping")  # test connection
        except Exception as exc:
            raise RuntimeError(f"MongoDB connection failed: {exc}")

        # ✅ Use database directly from URI
        db = client.get_default_database()

        if db is None:
            raise RuntimeError("Database name not found in MONGO_URI")

        app.mongo_client = client
        app.db = db


def get_db():
    if not hasattr(current_app, "db"):
        raise RuntimeError("Database not initialized. Call init_db first.")
    return current_app.db