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
    last_feedback = "Get ready for squats!"
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
                
                # Get hip, knee, and ankle landmarks
                left_hip = landmarks[md_pose.PoseLandmark.LEFT_HIP]
                right_hip = landmarks[md_pose.PoseLandmark.RIGHT_HIP]
                left_knee = landmarks[md_pose.PoseLandmark.LEFT_KNEE]
                right_knee = landmarks[md_pose.PoseLandmark.RIGHT_KNEE]
                left_ankle = landmarks[md_pose.PoseLandmark.LEFT_ANKLE]
                right_ankle = landmarks[md_pose.PoseLandmark.RIGHT_ANKLE]
                
                # Calculate knee angles
                left_angle = math.degrees(math.atan2(
                    left_ankle.y - left_knee.y,
                    left_ankle.x - left_knee.x
                ) - math.atan2(
                    left_hip.y - left_knee.y,
                    left_hip.x - left_knee.x
                ))
                right_angle = math.degrees(math.atan2(
                    right_ankle.y - right_knee.y,
                    right_ankle.x - right_knee.x
                ) - math.atan2(
                    right_hip.y - right_knee.y,
                    right_hip.x - right_knee.x
                ))
                
                # Check form and provide feedback
                if abs(left_angle - right_angle) > 15:
                    form_status = "warning"
                    last_feedback = "Keep your knees aligned"
                elif left_angle > 160 and right_angle > 160:
                    if position != "up":
                        position = "up"
                        if form_status == "good":
                            last_feedback = "Good form! Now go down slowly"
                        else:
                            last_feedback = "Fix your form before continuing"
                elif left_angle < 90 and right_angle < 90:
                    if position == "up":
                        if form_status == "good":
                            position = "down"
                            count += 1
                            last_feedback = f"Great! {count} squats completed. Keep going!"
                        else:
                            last_feedback = "Fix your form before continuing"
                else:
                    form_status = "good"
                    if position == "up":
                        last_feedback = "Go lower for a proper squat"
                    elif position == "down":
                        last_feedback = "Stand up straight"

            else:
                last_feedback = "Cannot detect body position. Please ensure you're visible in the camera"

            # Break if we've counted 10 squats
            if count >= 10:
                return {"count": count, "feedback": "Great job! You've completed your squats!"}

            # Add a small delay to prevent high CPU usage
            time.sleep(0.1)

        # If we hit the timeout
        if count > 0:
            return {"count": count, "feedback": f"Time's up! You completed {count} squats. {last_feedback}"}
        else:
            return {"count": 0, "feedback": "No squats detected. Please ensure you're visible in the camera"}

    except Exception as e:
        logger.error(f"Error during squat detection: {str(e)}")
        return {"count": count, "feedback": f"Error: {str(e)}"}
    finally:
        if cap:
            cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    result = count_exercise()
    print(result)
