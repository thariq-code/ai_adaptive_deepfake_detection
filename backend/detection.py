# ===============================
# IMPORTS
# ===============================

from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from werkzeug.utils import secure_filename
import tempfile
import os

from database.mongo import get_db
from backend.detection_engine import DetectionEngine


# ===============================
# ENGINE INIT (ONLY ONCE)
# ===============================

engine = DetectionEngine()


# ===============================
# LIVE WEBCAM DETECTION
# ===============================

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
        "confidence": confidence,
        "source": "webcam"
    })

    return jsonify({
        "classification": classification,
        "fraud_score": fraud_score,
        "confidence": confidence
    }), 200


# ===============================
# VIDEO FILE DETECTION
# ===============================

@jwt_required()
def detect_video():
    user_id = get_jwt_identity()

    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "Empty filename"}), 400

    allowed = {'mp4', 'mov', 'avi'}

    if not ('.' in file.filename and
            file.filename.rsplit('.', 1)[1].lower() in allowed):
        return jsonify({"error": "Unsupported video format"}), 400

    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name

    try:
        classification, fraud_score, confidence = engine.process_video(tmp_path)

        db = get_db()
        db.history.insert_one({
            "user_id": user_id,
            "timestamp": datetime.utcnow(),
            "fraud_score": fraud_score,
            "classification": classification,
            "confidence": confidence,
            "source": "video"
        })

        return jsonify({
            "classification": classification,
            "fraud_score": fraud_score,
            "confidence": confidence
        }), 200

    finally:
        os.unlink(tmp_path)


# ===============================
# AUDIO FILE DETECTION
# ===============================

@jwt_required()
def detect_audio():
    user_id = get_jwt_identity()

    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "Empty filename"}), 400

    allowed = {'mp3', 'wav'}

    if not ('.' in file.filename and
            file.filename.rsplit('.', 1)[1].lower() in allowed):
        return jsonify({"error": "Unsupported audio format"}), 400

    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name

    try:
        classification, fraud_score, confidence = engine.process_audio(tmp_path)

        db = get_db()
        db.history.insert_one({
            "user_id": user_id,
            "timestamp": datetime.utcnow(),
            "fraud_score": fraud_score,
            "classification": classification,
            "confidence": confidence,
            "source": "audio"
        })

        return jsonify({
            "classification": classification,
            "fraud_score": fraud_score,
            "confidence": confidence
        }), 200

    finally:
        os.unlink(tmp_path)


# ===============================
# HISTORY
# ===============================

@jwt_required()
def history():
    user_id = get_jwt_identity()
    db = get_db()

    cursor = db.history.find(
        {"user_id": user_id}
    ).sort("timestamp", -1).limit(50)

    results = []

    for doc in cursor:
        results.append({
            "timestamp": doc["timestamp"].isoformat(),
            "fraud_score": doc["fraud_score"],
            "classification": doc["classification"],
            "confidence": doc.get("confidence", 0.0),
            "source": doc.get("source", "webcam")
        })

    return jsonify(results), 200


# ===============================
# DASHBOARD
# ===============================

@jwt_required()
def dashboard():
    user_id = get_jwt_identity()
    db = get_db()

    total = db.history.count_documents({"user_id": user_id})
    fraud = db.history.count_documents({
        "user_id": user_id,
        "classification": "FAKE"
    })
    real = db.history.count_documents({
        "user_id": user_id,
        "classification": "REAL"
    })
    suspicious = db.history.count_documents({
        "user_id": user_id,
        "classification": "SUSPICIOUS"
    })

    return jsonify({
        "total_detections": total,
        "fraud_count": fraud,
        "real_count": real,
        "suspicious_count": suspicious
    }), 200