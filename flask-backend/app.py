from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import importlib.util
import os
import sys
import time
import cv2
import logging
import platform
import socket
import threading
import redis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# CORS configuration
CORS(app)

# Initialize Redis connection for rate limiting
try:
    redis_client = redis.Redis(host='localhost', port=6379, db=0)
    redis_client.ping()  # Test connection
    logger.info("Successfully connected to Redis")
except redis.ConnectionError:
    logger.warning("Could not connect to Redis, falling back to memory storage")
    redis_client = None

# Configure rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    storage_uri="redis://localhost:6379" if redis_client else None,
    default_limits=["200 per day", "50 per hour"]
)

# Global camera lock to prevent concurrent access
camera_lock = threading.Lock()

# Global variables for exercise tracking
current_exercise = None
exercise_count = 0
exercise_feedback = ""
camera = None

# Allowed exercise scripts
ALLOWED_SCRIPTS = {
    'jumpingjacks': 'jumpingjacks',
    'pushups': 'pushups',
    'squats': 'squats',
    'yoga': 'yoga'
}

def get_camera():
    """Get camera with proper configuration based on platform."""
    global camera
    if camera is None:
        try:
            if platform.system() == 'Darwin':
                # Try Continuity Camera first
                camera = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)
                if not camera.isOpened():
                    # Fallback to regular camera
                    camera = cv2.VideoCapture(0)
            else:
                camera = cv2.VideoCapture(0)
            
            if not camera.isOpened():
                raise Exception("Could not open camera")
            
            # Set camera properties
            camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            camera.set(cv2.CAP_PROP_FPS, 30)
            
            logger.info("Successfully configured camera")
            return camera
        except Exception as e:
            logger.error(f"Error configuring camera: {str(e)}")
            if camera:
                camera.release()
                camera = None
            raise
    return camera

def generate_frames():
    """Video streaming generator function."""
    try:
        with camera_lock:
            camera = get_camera()
            while True:
                success, frame = camera.read()
                if not success:
                    logger.warning("Failed to read frame from camera")
                    break
                else:
                    # Flip the frame horizontally for a later selfie-view display
                    frame = cv2.flip(frame, 1)
                    
                    # Draw exercise count and feedback
                    cv2.putText(frame, f'Count: {exercise_count}', (10, 30), 
                              cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    if exercise_feedback:
                        # Split feedback into multiple lines if too long
                        words = exercise_feedback.split()
                        lines = []
                        current_line = []
                        for word in words:
                            current_line.append(word)
                            if len(' '.join(current_line)) > 30:  # max chars per line
                                lines.append(' '.join(current_line[:-1]))
                                current_line = [word]
                        if current_line:
                            lines.append(' '.join(current_line))
                        
                        for i, line in enumerate(lines):
                            cv2.putText(frame, line, (10, 60 + i*30),
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    
                    # Convert frame to jpg
                    ret, buffer = cv2.imencode('.jpg', frame)
                    frame = buffer.tobytes()
                    
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    except Exception as e:
        logger.error(f"Error in generate_frames: {str(e)}")
    finally:
        if camera:
            camera.release()
            camera = None

@app.route('/video_feed')
@limiter.limit("10 per second")
def video_feed():
    """Video streaming route."""
    return Response(generate_frames(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/status')
@limiter.limit("10 per second")
def get_status():
    """Get current exercise status."""
    return jsonify({
        'count': exercise_count,
        'feedback': exercise_feedback
    })

@app.route('/<exercise>', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def handle_exercise(exercise):
    """Handle exercise requests."""
    global current_exercise, exercise_count, exercise_feedback
    
    if exercise not in ALLOWED_SCRIPTS:
        return jsonify({'error': 'Invalid exercise'}), 400
    
    if request.method == 'GET':
        return jsonify({'message': f'Ready for {exercise}'})
    
    if request.method == 'POST':
        try:
            # Import the exercise module
            module_path = os.path.join(os.path.dirname(__file__), 'exercises', f'{exercise}.py')
            spec = importlib.util.spec_from_file_location(exercise, module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Run the exercise
            result = module.count_exercise()
            
            # Update global variables
            exercise_count = result.get('count', 0)
            exercise_feedback = result.get('feedback', '')
            
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error in {exercise}: {str(e)}")
            return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    logger.info("Starting Flask application...")
    app.run(host='0.0.0.0', port=5001, debug=True)
