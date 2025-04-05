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

def count_exercise():
    start_time = time.time()
    pose_start_time = None
    total_pose_time = 0
    last_feedback = "Get ready for the yoga pose!"
    form_status = "good"  # Can be "good", "warning", or "bad"
    target_duration = 30  # 30 seconds target

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
        while time.time() - start_time < 60:  # 60 seconds timeout
            success, image = cap.read()
            if not success:
                consecutive_failures += 1
                if consecutive_failures > 5:
                    return {"count": total_pose_time, "feedback": "Failed to read from camera consistently"}
                continue
            consecutive_failures = 0

            # Process frame
            image = cv2.cvtColor(cv2.flip(image, 1), cv2.COLOR_BGR2RGB)
            image.flags.writeable = False
            result = pose.process(image)
            image.flags.writeable = True

            if result.pose_landmarks:
                landmarks = result.pose_landmarks.landmark
                
                # Get key landmarks for pose detection
                left_shoulder = landmarks[md_pose.PoseLandmark.LEFT_SHOULDER]
                right_shoulder = landmarks[md_pose.PoseLandmark.RIGHT_SHOULDER]
                left_hip = landmarks[md_pose.PoseLandmark.LEFT_HIP]
                right_hip = landmarks[md_pose.PoseLandmark.RIGHT_HIP]
                left_knee = landmarks[md_pose.PoseLandmark.LEFT_KNEE]
                right_knee = landmarks[md_pose.PoseLandmark.RIGHT_KNEE]
                left_ankle = landmarks[md_pose.PoseLandmark.LEFT_ANKLE]
                right_ankle = landmarks[md_pose.PoseLandmark.RIGHT_ANKLE]
                
                # Calculate angles for pose detection
                shoulder_angle = math.degrees(math.atan2(
                    right_shoulder.y - left_shoulder.y,
                    right_shoulder.x - left_shoulder.x
                ))
                hip_angle = math.degrees(math.atan2(
                    right_hip.y - left_hip.y,
                    right_hip.x - left_hip.x
                ))
                
                # Check form and provide feedback
                if abs(shoulder_angle) > 10 or abs(hip_angle) > 10:
                    form_status = "warning"
                    last_feedback = "Keep your shoulders and hips level"
                else:
                    form_status = "good"
                    if pose_start_time is None:
                        pose_start_time = time.time()
                        last_feedback = "Good form! Hold the pose"
                    else:
                        current_pose_time = time.time() - pose_start_time
                        if current_pose_time > 1:  # Only count after 1 second of good form
                            total_pose_time = int(current_pose_time)
                            remaining_time = max(0, target_duration - total_pose_time)
                            last_feedback = f"Good form! Hold for {remaining_time} more seconds"
                if form_status == "warning":
                    pose_start_time = None
                    last_feedback = "Adjust your form to continue the timer"

            else:
                last_feedback = "Cannot detect body position. Please ensure you're visible in the camera"
                pose_start_time = None

            # Check if target duration is reached
            if total_pose_time >= target_duration:
                return {"count": total_pose_time, "feedback": "Great job! You've completed the pose!"}

            # Add a small delay to prevent high CPU usage
            time.sleep(0.1)

        # If we hit the timeout
        if total_pose_time > 0:
            return {"count": total_pose_time, "feedback": f"Time's up! You held the pose for {total_pose_time} seconds. {last_feedback}"}
        else:
            return {"count": 0, "feedback": "No pose detected. Please ensure you're visible in the camera"}

    except Exception as e:
        logger.error(f"Error during pose detection: {str(e)}")
        return {"count": total_pose_time, "feedback": f"Error: {str(e)}"}
    finally:
        if cap:
            cap.release()
        cv2.destroyAllWindows() 