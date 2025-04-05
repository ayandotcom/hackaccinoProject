import cv2
import math
import mediapipe as md
import time
import logging
from app import get_camera, camera_lock

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Importing necessary libraries
md_drawing = md.solutions.drawing_utils
md_drawing_style = md.solutions.drawing_styles
md_pose = md.solutions.pose

def count_exercise(update_callback=None):
    count = 0
    position = None
    start_time = time.time()
    timeout = 60  # 60 seconds timeout
    last_feedback = "Get ready for jumping jacks!"
    form_status = "good"  # Can be "good", "warning", or "bad"
    last_update_time = 0
    update_interval = 0.5  # Update every 0.5 seconds
    pose = None

    try:
        # Get the global camera instance
        with camera_lock:
            camera = get_camera()
            if not camera or not camera.isOpened():
                return {"count": 0, "feedback": "Could not access camera"}

            # Initialize pose detection with higher confidence thresholds
            pose = md_pose.Pose(
                min_detection_confidence=0.7,
                min_tracking_confidence=0.8,
                model_complexity=1
            )

            consecutive_failures = 0
            last_valid_pose_time = time.time()
            min_time_between_reps = 0.5  # Minimum time between reps to prevent double counting

            while time.time() - start_time < timeout:
                success, image = camera.read()
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
                    
                    # Get key landmarks
                    left_shoulder = landmarks[md_pose.PoseLandmark.LEFT_SHOULDER]
                    right_shoulder = landmarks[md_pose.PoseLandmark.RIGHT_SHOULDER]
                    left_hip = landmarks[md_pose.PoseLandmark.LEFT_HIP]
                    right_hip = landmarks[md_pose.PoseLandmark.RIGHT_HIP]
                    left_ankle = landmarks[md_pose.PoseLandmark.LEFT_ANKLE]
                    right_ankle = landmarks[md_pose.PoseLandmark.RIGHT_ANKLE]
                    left_wrist = landmarks[md_pose.PoseLandmark.LEFT_WRIST]
                    right_wrist = landmarks[md_pose.PoseLandmark.RIGHT_WRIST]
                    
                    # Calculate distances and angles
                    shoulder_distance = math.sqrt(
                        (right_shoulder.x - left_shoulder.x) ** 2 +
                        (right_shoulder.y - left_shoulder.y) ** 2
                    )
                    ankle_distance = math.sqrt(
                        (right_ankle.x - left_ankle.x) ** 2 +
                        (right_ankle.y - left_ankle.y) ** 2
                    )
                    wrist_distance = math.sqrt(
                        (right_wrist.x - left_wrist.x) ** 2 +
                        (right_wrist.y - left_wrist.y) ** 2
                    )

                    # Calculate vertical positions
                    wrist_height = (left_wrist.y + right_wrist.y) / 2
                    shoulder_height = (left_shoulder.y + right_shoulder.y) / 2
                    hip_height = (left_hip.y + right_hip.y) / 2

                    current_time = time.time()
                    
                    # Detect jumping jack position
                    if wrist_height < shoulder_height and ankle_distance > 0.2:
                        if position != "up" and current_time - last_valid_pose_time >= min_time_between_reps:
                            position = "up"
                            count += 1
                            last_valid_pose_time = current_time
                            last_feedback = "Good form! Keep going"
                            form_status = "good"
                    else:
                        position = "down"
                        if wrist_distance < 0.1 or ankle_distance < 0.1:
                            last_feedback = "Spread your arms and legs wider"
                            form_status = "warning"
                        elif wrist_height > shoulder_height:
                            last_feedback = "Raise your arms higher"
                            form_status = "warning"
                        else:
                            last_feedback = "Get ready for the next rep"
                            form_status = "good"

                    # Update callback if provided
                    if update_callback and current_time - last_update_time >= update_interval:
                        update_callback(count, last_feedback)
                        last_update_time = current_time
                else:
                    last_feedback = "Cannot detect body position. Please ensure you're visible in the camera"
                    form_status = "warning"

                # Add a small delay to prevent high CPU usage
                time.sleep(0.1)

            # If we hit the timeout
            if count > 0:
                return {"count": count, "feedback": f"Time's up! You completed {count} jumping jacks. {last_feedback}"}
            else:
                return {"count": 0, "feedback": "No jumping jacks detected. Please ensure you're visible in the camera"}

    except Exception as e:
        logger.error(f"Error during jumping jacks detection: {str(e)}")
        return {"count": count, "feedback": f"Error: {str(e)}"}
    finally:
        if pose:
            pose.close()

if __name__ == "__main__":
    result = count_exercise()
    print(result)
