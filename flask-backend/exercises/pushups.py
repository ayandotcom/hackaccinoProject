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
    last_feedback = "Get ready for pushups!"
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
                
                # Get shoulder, elbow, and wrist landmarks
                left_shoulder = landmarks[md_pose.PoseLandmark.LEFT_SHOULDER]
                right_shoulder = landmarks[md_pose.PoseLandmark.RIGHT_SHOULDER]
                left_elbow = landmarks[md_pose.PoseLandmark.LEFT_ELBOW]
                right_elbow = landmarks[md_pose.PoseLandmark.RIGHT_ELBOW]
                left_wrist = landmarks[md_pose.PoseLandmark.LEFT_WRIST]
                right_wrist = landmarks[md_pose.PoseLandmark.RIGHT_WRIST]
                
                # Calculate elbow angles
                left_angle = math.degrees(math.atan2(
                    left_wrist.y - left_elbow.y,
                    left_wrist.x - left_elbow.x
                ) - math.atan2(
                    left_shoulder.y - left_elbow.y,
                    left_shoulder.x - left_elbow.x
                ))
                right_angle = math.degrees(math.atan2(
                    right_wrist.y - right_elbow.y,
                    right_wrist.x - right_elbow.x
                ) - math.atan2(
                    right_shoulder.y - right_elbow.y,
                    right_shoulder.x - right_elbow.x
                ))
                
                # Check form and provide feedback
                if abs(left_angle - right_angle) > 15:
                    form_status = "warning"
                    last_feedback = "Keep your arms even for better form"
                elif position == "up" and (left_angle < 165 or right_angle < 165):
                    form_status = "warning"
                    last_feedback = "Extend your arms fully at the top"
                elif position == "down" and (left_angle > 85 or right_angle > 85):
                    form_status = "warning"
                    last_feedback = "Lower your body more for a full pushup"
                else:
                    form_status = "good"
                
                # Detect pushup position with more precise angles
                if left_angle > 165 and right_angle > 165:  # Up position
                    if position != "up":
                        position = "up"
                        if form_status == "good":
                            last_feedback = "Good form! Now go down slowly"
                elif left_angle < 85 and right_angle < 85:  # Down position
                    if position == "up":
                        if form_status == "good":
                            position = "down"
                            count += 1
                            last_feedback = f"Great! {count} pushups completed. Keep going!"
                        else:
                            last_feedback = "Fix your form before continuing"
            else:
                last_feedback = "Cannot detect body position. Please ensure you're visible in the camera"

            # Break if we've counted 10 pushups
            if count >= 10:
                return {"count": count, "feedback": "Great job! You've completed your pushups!"}

            # Add a small delay to prevent high CPU usage
            time.sleep(0.1)

        # If we hit the timeout
        if count > 0:
            return {"count": count, "feedback": f"Time's up! You completed {count} pushups. {last_feedback}"}
        else:
            return {"count": 0, "feedback": "No pushups detected. Please ensure you're visible in the camera"}

    except Exception as e:
        logger.error(f"Error during pushup detection: {str(e)}")
        return {"count": count, "feedback": f"Error: {str(e)}"}
    finally:
        if cap:
            cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    result = count_exercise()
    print(result)
