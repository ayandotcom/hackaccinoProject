import cv2
import math
import mediapipe as md
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Importing necessary libraries
md_drawing = md.solutions.drawing_utils
md_drawing_style = md.solutions.drawing_styles
md_pose = md.solutions.pose

def detect_pose(landmarks, pose_name):
    """Detect specific yoga poses based on body angles."""
    if pose_name == "tree":
        return detect_tree_pose(landmarks)
    elif pose_name == "warrior":
        return detect_warrior_pose(landmarks)
    elif pose_name == "downward_dog":
        return detect_downward_dog(landmarks)
    else:
        return {"is_correct": False, "feedback": "Unknown pose"}

def detect_tree_pose(landmarks):
    """Detect Tree Pose (Vrikshasana)."""
    try:
        # Get relevant landmarks
        left_hip = landmarks[md_pose.PoseLandmark.LEFT_HIP]
        right_hip = landmarks[md_pose.PoseLandmark.RIGHT_HIP]
        left_knee = landmarks[md_pose.PoseLandmark.LEFT_KNEE]
        right_knee = landmarks[md_pose.PoseLandmark.RIGHT_KNEE]
        left_ankle = landmarks[md_pose.PoseLandmark.LEFT_ANKLE]
        right_ankle = landmarks[md_pose.PoseLandmark.RIGHT_ANKLE]
        
        # Calculate angles
        left_leg_angle = math.degrees(math.atan2(
            left_ankle.y - left_knee.y,
            left_ankle.x - left_knee.x
        ) - math.atan2(
            left_hip.y - left_knee.y,
            left_hip.x - left_knee.x
        ))
        
        right_leg_angle = math.degrees(math.atan2(
            right_ankle.y - right_knee.y,
            right_ankle.x - right_knee.x
        ) - math.atan2(
            right_hip.y - right_knee.y,
            right_hip.x - right_knee.x
        ))
        
        # Check if one leg is straight and the other is bent
        if (left_leg_angle > 160 and right_leg_angle < 120) or (right_leg_angle > 160 and left_leg_angle < 120):
            return {
                "is_correct": True,
                "feedback": "Good Tree Pose! Keep your balance"
            }
        else:
            return {
                "is_correct": False,
                "feedback": "Bend one knee and place the foot on the inner thigh of the other leg"
            }
    except Exception as e:
        logger.error(f"Error in tree pose detection: {str(e)}")
        return {"is_correct": False, "feedback": "Error detecting pose"}

def detect_warrior_pose(landmarks):
    """Detect Warrior II Pose (Virabhadrasana II)."""
    try:
        # Get relevant landmarks
        left_hip = landmarks[md_pose.PoseLandmark.LEFT_HIP]
        right_hip = landmarks[md_pose.PoseLandmark.RIGHT_HIP]
        left_knee = landmarks[md_pose.PoseLandmark.LEFT_KNEE]
        right_knee = landmarks[md_pose.PoseLandmark.RIGHT_KNEE]
        left_ankle = landmarks[md_pose.PoseLandmark.LEFT_ANKLE]
        right_ankle = landmarks[md_pose.PoseLandmark.RIGHT_ANKLE]
        left_shoulder = landmarks[md_pose.PoseLandmark.LEFT_SHOULDER]
        right_shoulder = landmarks[md_pose.PoseLandmark.RIGHT_SHOULDER]
        
        # Calculate angles
        front_knee_angle = math.degrees(math.atan2(
            left_ankle.y - left_knee.y,
            left_ankle.x - left_knee.x
        ) - math.atan2(
            left_hip.y - left_knee.y,
            left_hip.x - left_knee.x
        ))
        
        # Check if front knee is bent at 90 degrees and arms are extended
        if 80 < front_knee_angle < 100:
            return {
                "is_correct": True,
                "feedback": "Good Warrior II! Keep your front knee at 90 degrees"
            }
        else:
            return {
                "is_correct": False,
                "feedback": "Bend your front knee to 90 degrees and extend your arms"
            }
    except Exception as e:
        logger.error(f"Error in warrior pose detection: {str(e)}")
        return {"is_correct": False, "feedback": "Error detecting pose"}

def detect_downward_dog(landmarks):
    """Detect Downward-Facing Dog Pose (Adho Mukha Svanasana)."""
    try:
        # Get relevant landmarks
        left_shoulder = landmarks[md_pose.PoseLandmark.LEFT_SHOULDER]
        right_shoulder = landmarks[md_pose.PoseLandmark.RIGHT_SHOULDER]
        left_hip = landmarks[md_pose.PoseLandmark.LEFT_HIP]
        right_hip = landmarks[md_pose.PoseLandmark.RIGHT_HIP]
        left_knee = landmarks[md_pose.PoseLandmark.LEFT_KNEE]
        right_knee = landmarks[md_pose.PoseLandmark.RIGHT_KNEE]
        
        # Calculate angles
        hip_angle = math.degrees(math.atan2(
            left_hip.y - right_hip.y,
            left_hip.x - right_hip.x
        ))
        
        # Check if hips are higher than shoulders and legs are straight
        if left_hip.y < left_shoulder.y and right_hip.y < right_shoulder.y:
            return {
                "is_correct": True,
                "feedback": "Good Downward Dog! Keep your spine straight"
            }
        else:
            return {
                "is_correct": False,
                "feedback": "Lift your hips higher and straighten your legs"
            }
    except Exception as e:
        logger.error(f"Error in downward dog detection: {str(e)}")
        return {"is_correct": False, "feedback": "Error detecting pose"}

def count_exercise():
    """Main function to detect and count yoga poses."""
    count = 0
    start_time = time.time()
    timeout = 60  # 60 seconds timeout
    last_feedback = "Get ready for yoga poses!"
    form_status = "good"
    current_pose = None
    pose_hold_time = 0
    required_hold_time = 3  # seconds

    # Try different camera indices
    cap = None
    for camera_index in [0, 1]:
        try:
            cap = cv2.VideoCapture(camera_index)
            if cap.isOpened():
                ret, test_frame = cap.read()
                if ret and test_frame is not None:
                    logger.info(f"Successfully opened camera at index {camera_index}")
                    break
                else:
                    cap.release()
                    cap = None
        except Exception as e:
            logger.warning(f"Failed to open camera at index {camera_index}: {e}")
            if cap:
                cap.release()
                cap = None

    if not cap:
        return {"count": 0, "feedback": "Could not open any camera"}

    # Initialize pose detection with higher confidence thresholds
    pose = md_pose.Pose(
        min_detection_confidence=0.7,
        min_tracking_confidence=0.8,
        model_complexity=1
    )

    try:
        consecutive_failures = 0
        while time.time() - start_time < timeout:
            success, image = cap.read()
            if not success:
                consecutive_failures += 1
                if consecutive_failures > 5:
                    return {"count": count, "feedback": "Failed to read from camera consistently"}
                continue
            consecutive_failures = 0

            # Process frame
            image = cv2.cvtColor(cv2.flip(image, 1), cv2.COLOR_BGR2RGB)
            image.flags.writeable = False
            result = pose.process(image)
            image.flags.writeable = True

            if result.pose_landmarks:
                # Detect current pose
                pose_result = detect_pose(result.pose_landmarks.landmark, "tree")  # Default to tree pose
                
                if pose_result["is_correct"]:
                    if current_pose != "tree":
                        current_pose = "tree"
                        pose_hold_time = time.time()
                    elif time.time() - pose_hold_time >= required_hold_time:
                        count += 1
                        last_feedback = f"Great! {count} poses completed. Hold for {required_hold_time} seconds each."
                        current_pose = None
                else:
                    last_feedback = pose_result["feedback"]
                    current_pose = None
            else:
                last_feedback = "Cannot detect body position. Please ensure you're visible in the camera"

            # Break if we've counted 5 poses
            if count >= 5:
                return {"count": count, "feedback": "Great job! You've completed your yoga session!"}

            # Add a small delay to prevent high CPU usage
            time.sleep(0.1)

        # If we hit the timeout
        if count > 0:
            return {"count": count, "feedback": f"Time's up! You completed {count} poses. {last_feedback}"}
        else:
            return {"count": 0, "feedback": "No poses detected. Please ensure you're visible in the camera"}

    except Exception as e:
        logger.error(f"Error during pose detection: {str(e)}")
        return {"count": count, "feedback": f"Error: {str(e)}"}
    finally:
        if cap:
            cap.release()
        cv2.destroyAllWindows() 