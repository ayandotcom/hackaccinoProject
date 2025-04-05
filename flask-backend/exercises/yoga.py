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

    # Initialize pose detection with balanced confidence thresholds
    pose = md_pose.Pose(
        min_detection_confidence=0.6,
        min_tracking_confidence=0.6,
        model_complexity=1
    )

    try:
        consecutive_failures = 0
        last_valid_pose_time = time.time()
        min_time_between_reps = 0.8  # Increased minimum time between reps
        last_position_time = time.time()
        position_hold_time = 0.3  # Time required to hold a position
        current_pose = None
        pose_start_time = None
        max_pose_duration = 30  # Maximum pose duration in seconds

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
                landmarks = result.pose_landmarks.landmark
                
                # Get key landmarks for yoga poses
                left_shoulder = landmarks[md_pose.PoseLandmark.LEFT_SHOULDER]
                right_shoulder = landmarks[md_pose.PoseLandmark.RIGHT_SHOULDER]
                left_hip = landmarks[md_pose.PoseLandmark.LEFT_HIP]
                right_hip = landmarks[md_pose.PoseLandmark.RIGHT_HIP]
                left_knee = landmarks[md_pose.PoseLandmark.LEFT_KNEE]
                right_knee = landmarks[md_pose.PoseLandmark.RIGHT_KNEE]
                left_ankle = landmarks[md_pose.PoseLandmark.LEFT_ANKLE]
                right_ankle = landmarks[md_pose.PoseLandmark.RIGHT_ANKLE]
                left_elbow = landmarks[md_pose.PoseLandmark.LEFT_ELBOW]
                right_elbow = landmarks[md_pose.PoseLandmark.RIGHT_ELBOW]
                left_wrist = landmarks[md_pose.PoseLandmark.LEFT_WRIST]
                right_wrist = landmarks[md_pose.PoseLandmark.RIGHT_WRIST]
                
                # Calculate angles with smoothing
                back_angle = abs(math.degrees(math.atan2(
                    (right_shoulder.y + left_shoulder.y) / 2 - (right_hip.y + left_hip.y) / 2,
                    (right_shoulder.x + left_shoulder.x) / 2 - (right_hip.x + left_hip.x) / 2
                )))
                
                # Calculate relative heights
                shoulder_height = (left_shoulder.y + right_shoulder.y) / 2
                hip_height = (left_hip.y + right_hip.y) / 2
                knee_height = (left_knee.y + right_knee.y) / 2
                ankle_height = (left_ankle.y + right_ankle.y) / 2

                current_time = time.time()

                # More forgiving yoga pose detection with hold time requirement
                if (back_angle < 15 and  # More forgiving back angle
                    abs(shoulder_height - hip_height) < 0.15 and  # More forgiving alignment
                    abs(hip_height - knee_height) < 0.15):  # More forgiving hip position
                    if current_pose != "yoga":
                        if current_time - last_position_time >= position_hold_time:
                            current_pose = "yoga"
                            if pose_start_time is None:
                                pose_start_time = current_time
                            last_feedback = "Good form! Hold the pose"
                            form_status = "good"
                            last_valid_pose_time = current_time
                    last_position_time = current_time
                else:
                    last_position_time = current_time  # Reset hold time
                    # Provide specific form feedback with more forgiving thresholds
                    if back_angle >= 15:
                        last_feedback = "Try to keep your back straighter"
                        form_status = "warning"
                    elif abs(shoulder_height - hip_height) >= 0.15:
                        last_feedback = "Keep your shoulders and hips aligned"
                        form_status = "warning"
                    elif abs(hip_height - knee_height) >= 0.15:
                        last_feedback = "Keep your hips level"
                        form_status = "warning"
                    else:
                        last_feedback = "Keep going, maintain control"
                        form_status = "warning"

                # Update count based on duration
                if current_pose == "yoga" and pose_start_time is not None:
                    elapsed_time = current_time - pose_start_time
                    if elapsed_time >= max_pose_duration:
                        count = max_pose_duration
                        return {"count": count, "feedback": "Great job! You've completed your yoga pose!"}
                    else:
                        count = int(elapsed_time)
                        last_feedback = f"Hold for {max_pose_duration - count} more seconds"
            else:
                last_feedback = "Cannot detect body position. Please ensure you're visible in the camera"
                form_status = "warning"

            # Add a small delay to prevent high CPU usage
            time.sleep(0.1)

        # If we hit the timeout
        if count > 0:
            return {"count": count, "feedback": f"Time's up! You held the pose for {count} seconds. {last_feedback}"}
        else:
            return {"count": 0, "feedback": "No pose detected. Please ensure you're visible in the camera"}

    except Exception as e:
        logger.error(f"Error during yoga pose detection: {str(e)}")
        return {"count": count, "feedback": f"Error: {str(e)}"}
    finally:
        if cap:
            cap.release()
        cv2.destroyAllWindows() 