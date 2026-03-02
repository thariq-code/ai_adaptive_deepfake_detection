from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from database.mongo import get_db
from backend.detection_engine import DetectionEngine
from datetime import datetime

engine = DetectionEngine()

@jwt_required()
def detect():
    user_id = get_jwt_identity()
    data = request.get_json()
    if not data or "image" not in data:
        return jsonify({"error": "No image provided"}), 400
    image_b64 = data["image"]
    classification, fraud_score, confidence = engine.analyze(user_id, image_b64)
    db = get_db()
    db.history.insert_one({
        "user_id": user_id,
        "timestamp": datetime.utcnow(),
        "fraud_score": fraud_score,
        "classification": classification,
        "confidence": confidence
    })
    return jsonify({
        "classification": classification,
        "fraud_score": fraud_score,
        "confidence": confidence
    }), 200

@jwt_required()
def history():
    user_id = get_jwt_identity()
    db = get_db()
    cursor = db.history.find({"user_id": user_id}).sort("timestamp", -1).limit(50)
    results = []
    for doc in cursor:
        results.append({
            "timestamp": doc["timestamp"].isoformat(),
            "fraud_score": doc["fraud_score"],
            "classification": doc["classification"],
            "confidence": doc.get("confidence", 0.0)
        })
    return jsonify(results), 200

@jwt_required()
def dashboard():
    user_id = get_jwt_identity()
    db = get_db()
    total = db.history.count_documents({"user_id": user_id})
    fraud = db.history.count_documents({"user_id": user_id, "classification": "FAKE"})
    real = db.history.count_documents({"user_id": user_id, "classification": "REAL"})
    suspicious = db.history.count_documents({"user_id": user_id, "classification": "SUSPICIOUS"})
    return jsonify({
        "total_detections": total,
        "fraud_count": fraud,
        "real_count": real,
        "suspicious_count": suspicious
    }), 200