import cv2
import numpy as np
import base64
import librosa
from collections import defaultdict


class DetectionEngine:
    def __init__(self):
        self.user_frame_buffer = defaultdict(list)
        self.max_buffer_size = 5

    # -------------------------
    # IMAGE DECODING
    # -------------------------

    def decode_base64_image(self, base64_str):
        try:
            if "," in base64_str:
                base64_str = base64_str.split(",")[1]
            img_bytes = base64.b64decode(base64_str)
            np_arr = np.frombuffer(img_bytes, np.uint8)
            img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            return img
        except Exception as e:
            print(f"Image decode error: {e}")
            return None

    # -------------------------
    # SPATIAL ANALYSIS
    # -------------------------

    def spatial_score(self, frame):
        if frame is None:
            return 0.5

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        blur_score = max(0, min(1, 1.0 - (laplacian_var / 500.0)))

        noise = np.std(gray) / 255.0

        hist_r = cv2.calcHist([frame], [0], None, [256], [0, 256]).flatten()
        hist_g = cv2.calcHist([frame], [1], None, [256], [0, 256]).flatten()
        hist_b = cv2.calcHist([frame], [2], None, [256], [0, 256]).flatten()

        hist_r /= (hist_r.sum() + 1e-10)
        hist_g /= (hist_g.sum() + 1e-10)
        hist_b /= (hist_b.sum() + 1e-10)

        entropy_r = -np.sum(hist_r * np.log(hist_r + 1e-10))
        entropy_g = -np.sum(hist_g * np.log(hist_g + 1e-10))
        entropy_b = -np.sum(hist_b * np.log(hist_b + 1e-10))

        max_entropy = np.log(256.0)
        avg_entropy_norm = ((entropy_r + entropy_g + entropy_b) / 3.0) / max_entropy

        spatial = (blur_score * 0.5 + noise * 0.25 + (1 - avg_entropy_norm) * 0.25)

        return min(1.0, max(0.0, spatial))

    # -------------------------
    # TEMPORAL ANALYSIS (LIVE)
    # -------------------------

    def temporal_score(self, user_id, current_spatial):
        buffer = self.user_frame_buffer[user_id]

        if len(buffer) < 2:
            self._update_buffer(user_id, current_spatial)
            return 0.5

        recent = buffer[-3:]
        variance = np.var(recent)
        temporal = min(1.0, variance * 5)

        self._update_buffer(user_id, current_spatial)
        return temporal

    def _update_buffer(self, user_id, score):
        buffer = self.user_frame_buffer[user_id]
        buffer.append(score)
        if len(buffer) > self.max_buffer_size:
            buffer.pop(0)

    # -------------------------
    # LIVE WEBCAM ANALYSIS
    # -------------------------

    def analyze(self, user_id, base64_image):
        frame = self.decode_base64_image(base64_image)

        if frame is None:
            return "ERROR", 0.0, 0.0

        spatial = self.spatial_score(frame)
        temporal = self.temporal_score(user_id, spatial)

        fraud_score = 0.6 * spatial + 0.4 * temporal

        raw_conf = 1.0 - abs(fraud_score - 0.5) * 2.0
        confidence = max(0.0, min(1.0, raw_conf))

        if confidence < 0.30:
            classification = "SUSPICIOUS"
        elif fraud_score < 0.40:
            classification = "REAL"
        elif fraud_score > 0.60:
            classification = "FAKE"
        else:
            classification = "SUSPICIOUS"

        return classification, round(fraud_score, 2), round(confidence, 2)

    # -------------------------
    # VIDEO FILE ANALYSIS
    # -------------------------

    def process_video(self, file_path):
        cap = cv2.VideoCapture(file_path)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        if frame_count == 0:
            return "ERROR", 0.0, 0.0

        sample_indices = np.linspace(0, frame_count - 1, min(20, frame_count), dtype=int)

        spatial_scores = []

        for idx in sample_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if ret:
                score = self.spatial_score(frame)
                spatial_scores.append(score)

        cap.release()

        if not spatial_scores:
            return "ERROR", 0.0, 0.0

        avg_spatial = np.mean(spatial_scores)
        std_spatial = np.std(spatial_scores)

        fraud_score = avg_spatial
        confidence = max(0, min(1, 1.0 - std_spatial))

        if fraud_score < 0.3:
            classification = "REAL"
        elif fraud_score > 0.7:
            classification = "FAKE"
        else:
            classification = "SUSPICIOUS"

        return classification, round(fraud_score, 2), round(confidence, 2)

    # -------------------------
    # AUDIO FILE ANALYSIS
    # -------------------------

    def process_audio(self, file_path):
        try:
            y, sr = librosa.load(file_path, sr=16000, duration=10)

            if len(y) == 0:
                return "ERROR", 0.0, 0.0

            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)

            mean_mfcc = np.mean(mfccs)
            std_mfcc = np.std(mfccs)

            norm_mean = (mean_mfcc + 500) / 1000
            norm_std = std_mfcc / 100

            fraud_score = min(1.0, max(0.0, 0.5 + 0.3 * norm_mean + 0.2 * norm_std))
            confidence = 0.7 + 0.3 * (1.0 - abs(norm_mean - 0.5))

            if fraud_score < 0.3:
                classification = "REAL"
            elif fraud_score > 0.7:
                classification = "FAKE"
            else:
                classification = "SUSPICIOUS"

            return classification, round(fraud_score, 2), round(confidence, 2)

        except Exception as e:
            print(f"Audio processing error: {e}")
            return "ERROR", 0.0, 0.0