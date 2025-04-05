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
import atexit
import signal
import numpy as np
import mediapipe as mp
from mediapipe import solutions
from mediapipe.framework.formats import landmark_pb2
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
mp_drawing_style = mp.solutions.drawing_styles

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
camera_initialized = False

# Allowed exercise scripts
ALLOWED_SCRIPTS = {
    'jumpingjacks': 'jumpingjacks',
    'pushups': 'pushups',
    'squats': 'squats',
    'yoga': 'yoga',
    'tree_pose': 'tree_pose',
    'triangle_pose': 'triangle_pose',
    'plank': 'plank'
}

def init_camera():
    """Initialize the camera with proper configuration."""
    global camera, camera_initialized
    
    with camera_lock:
        if camera_initialized and camera and camera.isOpened():
            return True  # Camera already initialized
            
        try:
            # Release existing camera if any
            if camera:
                camera.release()
                camera = None
            
            # Try different camera indices
            for i in range(0, 4):  # Try up to 4 camera indices
                try:
                    if platform.system() == 'Darwin':
                        camera = cv2.VideoCapture(i, cv2.CAP_AVFOUNDATION)
                    else:
                        camera = cv2.VideoCapture(i)
                    
                    if camera.isOpened():
                        # Set camera properties
                        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                        camera.set(cv2.CAP_PROP_FPS, 30)
                        
                        # Test camera by reading a frame
                        ret, frame = camera.read()
                        if ret and frame is not None:
                            logger.info(f"Successfully initialized camera at index {i}")
                            camera_initialized = True
                            return True
                        else:
                            camera.release()
                            camera = None
                except Exception as e:
                    logger.warning(f"Failed to initialize camera at index {i}: {e}")
                    if camera:
                        camera.release()
                        camera = None
            
            logger.error("Could not initialize any camera")
            camera_initialized = False
            return False
            
        except Exception as e:
            logger.error(f"Error initializing camera: {e}")
            camera_initialized = False
            return False

def get_camera():
    """Get the camera instance, initializing if necessary."""
    with camera_lock:
        if not camera_initialized or not camera or not camera.isOpened():
            if not init_camera():
                raise Exception("Camera not available")
        return camera

def generate_frames():
    """Video streaming generator function."""
    consecutive_errors = 0
    max_consecutive_errors = 5
    frame_interval = 0.033  # ~30fps
    last_frame_time = 0
    frame_buffer = None
    pose = mp_pose.Pose(
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
        model_complexity=1
    )
    
    while True:
        try:
            current_time = time.time()
            if current_time - last_frame_time < frame_interval:
                time.sleep(0.001)  # Short sleep to prevent CPU overuse
                continue
                
            with camera_lock:
                camera = get_camera()
                if not camera or not camera.isOpened():
                    logger.error("Camera not available")
                    consecutive_errors += 1
                    if consecutive_errors >= max_consecutive_errors:
                        logger.error("Too many consecutive camera errors, stopping stream")
                        break
                    time.sleep(1)  # Wait before retrying
                    continue
                
                # Clear the buffer by reading multiple frames
                for _ in range(2):
                    camera.grab()
                success, frame = camera.read()
                
                if not success:
                    logger.warning("Failed to read frame from camera")
                    consecutive_errors += 1
                    if consecutive_errors >= max_consecutive_errors:
                        logger.error("Too many consecutive frame read errors, stopping stream")
                        break
                    time.sleep(0.1)  # Short delay before retrying
                    continue
                
                consecutive_errors = 0  # Reset error count on successful frame read
                last_frame_time = current_time
                
                # Flip the frame horizontally for a later selfie-view display
                frame = cv2.flip(frame, 1)
                
                # Process frame for pose detection
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame_rgb.flags.writeable = False
                results = pose.process(frame_rgb)
                frame_rgb.flags.writeable = True
                
                # Draw pose landmarks if detected
                if results.pose_landmarks:
                    mp_drawing.draw_landmarks(
                        frame,
                        results.pose_landmarks,
                        mp_pose.POSE_CONNECTIONS,
                        landmark_drawing_spec=mp_drawing_style.get_default_pose_landmarks_style()
                    )
                    # Add text to indicate person detected
                    cv2.putText(frame, "Person Detected", (10, 30),
                              cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                else:
                    cv2.putText(frame, "No Person Detected", (10, 30),
                              cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                
                # Draw exercise count and feedback
                cv2.putText(frame, f'Count: {exercise_count}', (10, 70), 
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
                        cv2.putText(frame, line, (10, 100 + i*30),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                # Convert frame to jpg with error handling
                try:
                    # Only encode if the frame has changed
                    if frame_buffer is None or not np.array_equal(frame, frame_buffer):
                        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                        if not ret:
                            logger.warning("Failed to encode frame")
                            continue
                        frame_buffer = frame.copy()
                        frame_bytes = buffer.tobytes()
                        
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                except Exception as e:
                    logger.error(f"Error encoding frame: {str(e)}")
                    continue
                
        except Exception as e:
            logger.error(f"Error in generate_frames: {str(e)}")
            consecutive_errors += 1
            if consecutive_errors >= max_consecutive_errors:
                logger.error("Too many consecutive errors, stopping stream")
                break
            time.sleep(1)  # Wait before retrying
    pose.close()

@app.route('/video_feed')
@limiter.limit("10 per second")
def video_feed():
    """Video streaming route."""
    try:
        response = Response(generate_frames(),
                          mimetype='multipart/x-mixed-replace; boundary=frame')
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        response.headers['Connection'] = 'close'
        return response
    except Exception as e:
        logger.error(f"Error in video_feed route: {str(e)}")
        return jsonify({'error': 'Failed to start video stream'}), 500

@app.route('/status')
@limiter.limit("10 per second")
def get_status():
    """Get current exercise status."""
    return jsonify({
        'count': exercise_count,
        'feedback': exercise_feedback
    })

@app.route('/<exercise>', methods=['POST'])
@limiter.limit("10 per minute")
def start_exercise(exercise):
    """Start a specific exercise."""
    global current_exercise, exercise_count, exercise_feedback
    
    if exercise not in ALLOWED_SCRIPTS:
        return jsonify({'error': 'Invalid exercise'}), 400
    
    try:
        # Reset exercise state
        exercise_count = 0
        exercise_feedback = "Starting exercise..."
        current_exercise = exercise
        
        # Import the exercise module
        module_name = f'exercises.{ALLOWED_SCRIPTS[exercise]}'
        spec = importlib.util.spec_from_file_location(
            module_name,
            os.path.join(os.path.dirname(__file__), f'exercises/{ALLOWED_SCRIPTS[exercise]}.py')
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Run the exercise with a callback to update state
        def update_state(count, feedback):
            global exercise_count, exercise_feedback
            exercise_count = count
            exercise_feedback = feedback
        
        # Run the exercise with the update callback
        result = module.count_exercise(update_callback=update_state)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error running exercise {exercise}: {str(e)}")
        return jsonify({'error': str(e)}), 500

def cleanup():
    """Clean up resources."""
    global camera, camera_initialized
    with camera_lock:
        try:
            if camera:
                camera.release()
                camera = None
            camera_initialized = False
            cv2.destroyAllWindows()
            logger.info("Cleaned up camera resources")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

def is_port_in_use(port):
    """Check if a port is already in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('127.0.0.1', port))
            return False
        except socket.error:
            return True

def setup_redis():
    """Setup Redis connection with retry logic."""
    global redis_client
    max_retries = 3
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            redis_client = redis.Redis(host='localhost', port=6379, db=0, socket_timeout=5)
            redis_client.ping()  # Test connection
            logger.info("Successfully connected to Redis")
            return True
        except redis.ConnectionError as e:
            logger.warning(f"Failed to connect to Redis (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                logger.warning("Could not connect to Redis, falling back to memory storage")
                redis_client = None
                return False

def signal_handler(signum, frame):
    """Handle termination signals."""
    logger.info("Received termination signal, cleaning up...")
    cleanup()
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Register cleanup function
atexit.register(cleanup)

if __name__ == '__main__':
    try:
        # Check if port is already in use
        if is_port_in_use(5001):
            logger.error("Port 5001 is already in use. Please stop any running instances.")
            sys.exit(1)
            
        # Setup Redis
        setup_redis()
        
        # Initialize camera
        init_camera()
        
        # Run the application
        app.run(host='0.0.0.0', port=5001, debug=True, use_reloader=False)
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
    finally:
        cleanup()
