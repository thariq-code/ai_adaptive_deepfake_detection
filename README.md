# AI-Based Adaptive Deepfake Voice and Video Scam Detection

Production-ready web application that detects deepfake media using intelligent adaptive fraud scoring.

## Tech Stack
- Backend: Python, Flask, MongoDB, OpenCV, NumPy
- Frontend: HTML5, CSS3, Vanilla JavaScript
- Authentication: JWT + bcrypt

## Setup
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set environment variables:
   - `MONGO_URI` (MongoDB connection string)
   - `JWT_SECRET_KEY` (secret for JWT)
4. Run: `python app.py`

## Deployment (Render)
- Connect GitHub repository
- Set build command: `pip install -r requirements.txt`
- Set start command: `gunicorn app:app`
- Add environment variables in Render dashboard

## Features
- User registration/login with JWT
- Live webcam capture and frame analysis
- Adaptive fraud scoring (spatial + temporal heuristics)
- Detection history and dashboard statistics
- Dark cybersecurity UI with animations