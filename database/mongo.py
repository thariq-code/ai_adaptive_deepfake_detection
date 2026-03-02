from pymongo import MongoClient
from flask import current_app


def init_db(app):
    with app.app_context():
        configured_uri = app.config.get("MONGO_URI")
        tried_uris = [configured_uri, "mongodb://localhost:27017/deepfake_db"]
        client = None
        success_uri = None
        for uri in tried_uris:
            try:
                client = MongoClient(uri, serverSelectionTimeoutMS=5000)
                client.admin.command("ping")
                success_uri = uri
                break
            except Exception as exc:
                print(f"MongoDB connection failed for {uri!r}: {exc}")

        if client is None or success_uri is None:
            raise RuntimeError(
                "Unable to connect to MongoDB. Ensure MongoDB is running locally or set a valid MONGO_URI."
            )

        db_name = success_uri.rsplit("/", 1)[-1] if "/" in success_uri else "deepfake_db"
        app.mongo_client = client
        app.db = client[db_name]


def get_db():
    if not hasattr(current_app, "db"):
        raise RuntimeError("Database not initialized. Call init_db first.")
    return current_app.db