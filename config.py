import os

class Config:
    MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/deepfake_db")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "super-secret-key-change-in-production")
    JWT_ACCESS_TOKEN_EXPIRES = 3600