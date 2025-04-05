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
    count = 0
    position = None
    start_time = time.time()
    timeout = 60  # 60 seconds timeout
    last_feedback = "Get ready for jumping jacks!"
    form_status = "good"  # Can be "good", "warning", or "bad"

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
                landmarks = result.pose_landmarks.landmark
                
                # Get shoulder and hip landmarks
                left_shoulder = landmarks[md_pose.PoseLandmark.LEFT_SHOULDER]
                right_shoulder = landmarks[md_pose.PoseLandmark.RIGHT_SHOULDER]
                left_hip = landmarks[md_pose.PoseLandmark.LEFT_HIP]
                right_hip = landmarks[md_pose.PoseLandmark.RIGHT_HIP]
                left_ankle = landmarks[md_pose.PoseLandmark.LEFT_ANKLE]
                right_ankle = landmarks[md_pose.PoseLandmark.RIGHT_ANKLE]
                
                # Calculate shoulder and hip angles
                shoulder_angle = math.degrees(math.atan2(
                    right_shoulder.y - left_shoulder.y,
                    right_shoulder.x - left_shoulder.x
                ))
                hip_angle = math.degrees(math.atan2(
                    right_hip.y - left_hip.y,
                    right_hip.x - left_hip.x
                ))
                
                # Check form and provide feedback
                if abs(shoulder_angle) < 45 and abs(hip_angle) < 45:
                    if position != "down":
                        position = "down"
                        if form_status == "good":
                            count += 1
                            last_feedback = f"Great! {count} jumping jacks completed. Keep going!"
                        else:
                            last_feedback = "Fix your form before continuing"
                elif abs(shoulder_angle) > 45 and abs(hip_angle) > 45:
                    if position != "up":
                        position = "up"
                        if form_status == "good":
                            last_feedback = "Good form! Now bring your arms and legs back together"
                        else:
                            last_feedback = "Keep your arms and legs straight"
                
                # Form checks
                if abs(shoulder_angle - hip_angle) > 15:
                    form_status = "warning"
                    last_feedback = "Keep your arms and legs moving together"
                elif abs(shoulder_angle) < 30 or abs(hip_angle) < 30:
                    form_status = "warning"
                    last_feedback = "Extend your arms and legs fully"
                else:
                    form_status = "good"

            else:
                last_feedback = "Cannot detect body position. Please ensure you're visible in the camera"

            # Break if we've counted 10 jumping jacks
            if count >= 10:
                return {"count": count, "feedback": "Great job! You've completed your jumping jacks!"}

            # Add a small delay to prevent high CPU usage
            time.sleep(0.1)

        # If we hit the timeout
        if count > 0:
            return {"count": count, "feedback": f"Time's up! You completed {count} jumping jacks. {last_feedback}"}
        else:
            return {"count": 0, "feedback": "No jumping jacks detected. Please ensure you're visible in the camera"}

    except Exception as e:
        logger.error(f"Error during jumping jack detection: {str(e)}")
        return {"count": count, "feedback": f"Error: {str(e)}"}
    finally:
        if cap:
            cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    result = count_exercise()
    print(result)
