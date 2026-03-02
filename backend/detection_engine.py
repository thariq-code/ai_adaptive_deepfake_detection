import cv2
import numpy as np
import base64
from collections import defaultdict

class DetectionEngine:
    def __init__(self):
        self.user_frame_buffer = defaultdict(list)
        self.max_buffer_size = 5

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

    def spatial_score(self, frame):
        if frame is None:
            return 0.5
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        blur_score = max(0, min(1, 1.0 - (laplacian_var / 500.0)))
        noise = np.std(gray) / 255.0
        hist_r = cv2.calcHist([frame], [0], None, [256], [0,256]).flatten()
        hist_g = cv2.calcHist([frame], [1], None, [256], [0,256]).flatten()
        hist_b = cv2.calcHist([frame], [2], None, [256], [0,256]).flatten()
        # normalize histograms to probability distributions
        hist_r = hist_r / (hist_r.sum() + 1e-10)
        hist_g = hist_g / (hist_g.sum() + 1e-10)
        hist_b = hist_b / (hist_b.sum() + 1e-10)
        entropy_r = -np.sum(hist_r * np.log(hist_r + 1e-10))
        entropy_g = -np.sum(hist_g * np.log(hist_g + 1e-10))
        entropy_b = -np.sum(hist_b * np.log(hist_b + 1e-10))
        # normalize entropy to [0,1] by dividing by log(256)
        max_entropy = np.log(256.0)
        avg_entropy_norm = ((entropy_r + entropy_g + entropy_b) / 3.0) / (max_entropy + 1e-10)
        spatial = (blur_score * 0.5 + noise * 0.25 + (1 - avg_entropy_norm) * 0.25)
        return min(1.0, max(0.0, spatial))

    def temporal_score(self, user_id, current_spatial):
        buffer = self.user_frame_buffer[user_id]
        if len(buffer) < 2:
            self._update_buffer(user_id, current_spatial)
            return 0.5
        recent = buffer[-3:]
        if len(recent) < 2:
            return 0.5
        variance = np.var(recent)
        temporal = min(1.0, variance * 5)
        self._update_buffer(user_id, current_spatial)
        return temporal

    def _update_buffer(self, user_id, score):
        buffer = self.user_frame_buffer[user_id]
        buffer.append(score)
        if len(buffer) > self.max_buffer_size:
            buffer.pop(0)

    def analyze(self, user_id, base64_image):
        frame = self.decode_base64_image(base64_image)
        if frame is None:
            return "ERROR", 0.0, 0.0
        spatial = self.spatial_score(frame)
        temporal = self.temporal_score(user_id, spatial)
        fraud_score = 0.6 * spatial + 0.4 * temporal
        # confidence: higher when fraud_score is near 0 or 1, lower near 0.5
        raw_conf = 1.0 - abs(fraud_score - 0.5) * 2.0
        confidence = max(0.0, min(1.0, raw_conf))
        print(f"[Detection] user={user_id} spatial={spatial:.3f} temporal={temporal:.3f} fraud={fraud_score:.3f} conf={confidence:.3f}")

        # updated thresholds per user feedback:
        # - treat low confidence (<0.30) as automatically suspicious
        # - REAL when fraud_score < 0.40 and confidence >= 0.30
        # - FAKE when fraud_score > 0.60 and confidence >= 0.30
        # - otherwise mark SUSPICIOUS
        if confidence < 0.30:
            classification = "SUSPICIOUS"
        elif fraud_score < 0.40:
            classification = "REAL"
        elif fraud_score > 0.60:
            classification = "FAKE"
        else:
            classification = "SUSPICIOUS"

        return classification, round(fraud_score, 2), round(confidence, 2)