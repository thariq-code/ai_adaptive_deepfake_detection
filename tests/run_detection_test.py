import sys
import base64
import cv2

from backend.detection_engine import DetectionEngine


def image_to_data_url(path: str) -> str:
    img = cv2.imread(path)
    if img is None:
        raise SystemExit(f"Failed to read image: {path}")
    success, buf = cv2.imencode('.jpg', img, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
    if not success:
        raise SystemExit("Failed to encode image to JPEG")
    b64 = base64.b64encode(buf.tobytes()).decode('utf-8')
    return f"data:image/jpeg;base64,{b64}"


def main():
    if len(sys.argv) < 2:
        print("Usage: python tests/run_detection_test.py path/to/image.jpg")
        raise SystemExit(1)

    img_path = sys.argv[1]
    data_url = image_to_data_url(img_path)

    engine = DetectionEngine()
    classification, fraud_score, confidence = engine.analyze("test_user", data_url)
    print("--- Detection Test Result ---")
    print(f"image: {img_path}")
    print(f"classification: {classification}")
    print(f"fraud_score: {fraud_score}")
    print(f"confidence: {confidence}")


if __name__ == '__main__':
    main()
