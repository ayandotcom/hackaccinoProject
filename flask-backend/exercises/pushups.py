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

def count_exercise():
    count = 0
    position = None
    start_time = time.time()
    timeout = 60  # 60 seconds timeout
    last_feedback = "Get ready for pushups!"
    form_status = "good"  # Can be "good", "warning", or "bad"

    # Get the global camera instance
    with camera_lock:
        camera = get_camera()
        if not camera or not camera.isOpened():
            return {"count": 0, "feedback": "Could not access camera"}

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
                    left_elbow = landmarks[md_pose.PoseLandmark.LEFT_ELBOW]
                    right_elbow = landmarks[md_pose.PoseLandmark.RIGHT_ELBOW]
                    left_wrist = landmarks[md_pose.PoseLandmark.LEFT_WRIST]
                    right_wrist = landmarks[md_pose.PoseLandmark.RIGHT_WRIST]
                    left_hip = landmarks[md_pose.PoseLandmark.LEFT_HIP]
                    right_hip = landmarks[md_pose.PoseLandmark.RIGHT_HIP]
                    left_ankle = landmarks[md_pose.PoseLandmark.LEFT_ANKLE]
                    right_ankle = landmarks[md_pose.PoseLandmark.RIGHT_ANKLE]
                    
                    # Calculate angles with smoothing
                    left_elbow_angle = abs(math.degrees(math.atan2(
                        left_wrist.y - left_elbow.y,
                        left_wrist.x - left_elbow.x
                    ) - math.atan2(
                        left_shoulder.y - left_elbow.y,
                        left_shoulder.x - left_elbow.x
                    )))
                    right_elbow_angle = abs(math.degrees(math.atan2(
                        right_wrist.y - right_elbow.y,
                        right_wrist.x - right_elbow.x
                    ) - math.atan2(
                        right_shoulder.y - right_elbow.y,
                        right_shoulder.x - right_elbow.x
                    )))

                    # Average the angles for more stability
                    elbow_angle = (left_elbow_angle + right_elbow_angle) / 2

                    # Calculate back angle and alignment
                    back_angle = abs(math.degrees(math.atan2(
                        (right_shoulder.y + left_shoulder.y) / 2 - (right_hip.y + left_hip.y) / 2,
                        (right_shoulder.x + left_shoulder.x) / 2 - (right_hip.x + left_hip.x) / 2
                    )))
                    hip_height = (left_hip.y + right_hip.y) / 2
                    ankle_height = (left_ankle.y + right_ankle.y) / 2

                    current_time = time.time()

                    # More forgiving pushup position detection with hold time requirement
                    if (elbow_angle < 100 and  # More forgiving down position
                        back_angle < 40 and  # More forgiving back angle
                        hip_height < ankle_height + 0.1):  # Slightly more forgiving hip position
                        if position != "down":
                            if current_time - last_position_time >= position_hold_time:
                                position = "down"
                                last_feedback = "Good form! Now push up"
                                form_status = "good"
                                last_valid_pose_time = current_time
                        last_position_time = current_time
                    elif (elbow_angle > 140 and  # More forgiving up position
                          back_angle < 40 and
                          hip_height < ankle_height + 0.1):
                        if position == "down":
                            if current_time - last_position_time >= position_hold_time:
                                if current_time - last_valid_pose_time > min_time_between_reps:
                                    count += 1
                                    position = "up"
                                    last_feedback = f"Great! {count} pushups completed"
                                    form_status = "good"
                                    last_valid_pose_time = current_time
                        last_position_time = current_time
                    else:
                        last_position_time = current_time  # Reset hold time
                        # Provide specific form feedback with more forgiving thresholds
                        if back_angle >= 40:
                            last_feedback = "Try to keep your back straighter"
                            form_status = "warning"
                        elif hip_height >= ankle_height + 0.1:
                            last_feedback = "Lower your hips slightly"
                            form_status = "warning"
                        elif abs(left_elbow_angle - right_elbow_angle) > 30:
                            last_feedback = "Try to keep your arms more even"
                            form_status = "warning"
                        elif elbow_angle >= 100 and position == "down":
                            last_feedback = "Try to go a bit lower"
                            form_status = "warning"
                        else:
                            last_feedback = "Keep going, maintain control"
                            form_status = "warning"
                else:
                    last_feedback = "Cannot detect body position. Please ensure you're visible in the camera"
                    form_status = "warning"

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
            pose.close()

if __name__ == "__main__":
    result = count_exercise()
    print(result)
