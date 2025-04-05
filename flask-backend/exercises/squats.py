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
    last_feedback = "Get ready for squats!"
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
                    
                    # Get key landmarks for squats
                    left_hip = landmarks[md_pose.PoseLandmark.LEFT_HIP]
                    right_hip = landmarks[md_pose.PoseLandmark.RIGHT_HIP]
                    left_knee = landmarks[md_pose.PoseLandmark.LEFT_KNEE]
                    right_knee = landmarks[md_pose.PoseLandmark.RIGHT_KNEE]
                    left_ankle = landmarks[md_pose.PoseLandmark.LEFT_ANKLE]
                    right_ankle = landmarks[md_pose.PoseLandmark.RIGHT_ANKLE]
                    left_shoulder = landmarks[md_pose.PoseLandmark.LEFT_SHOULDER]
                    right_shoulder = landmarks[md_pose.PoseLandmark.RIGHT_SHOULDER]
                    
                    # Calculate angles with smoothing
                    left_knee_angle = abs(math.degrees(math.atan2(
                        left_hip.y - left_knee.y,
                        left_hip.x - left_knee.x
                    ) - math.atan2(
                        left_ankle.y - left_knee.y,
                        left_ankle.x - left_knee.x
                    )))
                    right_knee_angle = abs(math.degrees(math.atan2(
                        right_hip.y - right_knee.y,
                        right_hip.x - right_knee.x
                    ) - math.atan2(
                        right_ankle.y - right_knee.y,
                        right_ankle.x - right_knee.x
                    )))

                    # Average the angles for more stability
                    knee_angle = (left_knee_angle + right_knee_angle) / 2

                    # Calculate hip height relative to knees
                    hip_height = (left_hip.y + right_hip.y) / 2
                    knee_height = (left_knee.y + right_knee.y) / 2
                    shoulder_height = (left_shoulder.y + right_shoulder.y) / 2

                    current_time = time.time()

                    # More forgiving squat position detection with hold time requirement
                    if (knee_angle < 110 and  # More forgiving down position
                        hip_height > knee_height - 0.1):  # More forgiving depth check
                        if position != "down":
                            if current_time - last_position_time >= position_hold_time:
                                position = "down"
                                last_feedback = "Good depth! Now stand up"
                                form_status = "good"
                                last_valid_pose_time = current_time
                        last_position_time = current_time
                    elif (knee_angle > 150 and  # More forgiving up position
                          abs(shoulder_height - hip_height) < 0.2):  # Check for upright position
                        if position == "down":
                            if current_time - last_position_time >= position_hold_time:
                                if current_time - last_valid_pose_time > min_time_between_reps:
                                    count += 1
                                    position = "up"
                                    last_feedback = f"Great! {count} squats completed"
                                    form_status = "good"
                                    last_valid_pose_time = current_time
                        last_position_time = current_time
                    else:
                        last_position_time = current_time  # Reset hold time
                        # Provide specific form feedback with more forgiving thresholds
                        if knee_angle >= 110 and position == "down":
                            last_feedback = "Try to go a bit lower"
                            form_status = "warning"
                        elif abs(left_knee_angle - right_knee_angle) > 20:
                            last_feedback = "Try to keep your knees even"
                            form_status = "warning"
                        elif abs(shoulder_height - hip_height) >= 0.2:
                            last_feedback = "Try to keep your back more upright"
                            form_status = "warning"
                        else:
                            last_feedback = "Keep going, maintain control"
                            form_status = "warning"
                else:
                    last_feedback = "Cannot detect body position. Please ensure you're visible in the camera"
                    form_status = "warning"

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
            pose.close()

if __name__ == "__main__":
    result = count_exercise()
    print(result)
