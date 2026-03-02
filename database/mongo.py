from pymongo import MongoClient
from flask import current_app

def init_db(app):
    with app.app_context():
        mongo_uri = app.config.get("MONGO_URI")

        try:
            client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
            client.admin.command("ping")
        except Exception as exc:
            raise RuntimeError(f"MongoDB connection failed: {exc}")

        # Direct database selection
        db = client["deepfake_db"]

        app.mongo_client = client
        app.db = db

def get_db():
    return current_app.db