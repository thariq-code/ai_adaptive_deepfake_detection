import bcrypt
from flask_jwt_extended import create_access_token
from database.mongo import get_db

def hash_password(password):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def check_password(hashed, password):
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

def create_user(email, password):
    db = get_db()
    if db.users.find_one({"email": email}):
        return None
    hashed = hash_password(password)
    user_id = db.users.insert_one({"email": email, "password": hashed}).inserted_id
    return str(user_id)

def authenticate_user(email, password):
    db = get_db()
    user = db.users.find_one({"email": email})
    if user and check_password(user["password"], password):
        return str(user["_id"])
    return None

def generate_token(user_id):
    return create_access_token(identity=user_id)