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
    start_time = time.time()
    pose_start_time = None
    total_pose_time = 0
    last_feedback = "Get ready for the plank!"
    form_status = "good"  # Can be "good", "warning", or "bad"
    target_duration = 30  # 30 seconds target
    min_time_for_valid_pose = 0.5  # Minimum time to hold good form before counting

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
            start_plank_time = None
            max_plank_duration = 30  # Maximum plank duration in seconds

            while time.time() - start_time < 60:  # 60 seconds timeout
                success, image = camera.read()
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
                    
                    # Get key landmarks for plank
                    left_shoulder = landmarks[md_pose.PoseLandmark.LEFT_SHOULDER]
                    right_shoulder = landmarks[md_pose.PoseLandmark.RIGHT_SHOULDER]
                    left_hip = landmarks[md_pose.PoseLandmark.LEFT_HIP]
                    right_hip = landmarks[md_pose.PoseLandmark.RIGHT_HIP]
                    left_knee = landmarks[md_pose.PoseLandmark.LEFT_KNEE]
                    right_knee = landmarks[md_pose.PoseLandmark.RIGHT_KNEE]
                    left_ankle = landmarks[md_pose.PoseLandmark.LEFT_ANKLE]
                    right_ankle = landmarks[md_pose.PoseLandmark.RIGHT_ANKLE]
                    
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

                    # More forgiving plank position detection with hold time requirement
                    if (back_angle < 10 and  # More forgiving back angle
                        abs(shoulder_height - hip_height) < 0.1 and  # More forgiving alignment
                        abs(hip_height - knee_height) < 0.1):  # More forgiving hip position
                        if pose_start_time is None:
                            pose_start_time = current_time
                        last_feedback = "Good form! Hold the position"
                        form_status = "good"
                        last_valid_pose_time = current_time
                    else:
                        pose_start_time = None
                        # Provide specific form feedback with more forgiving thresholds
                        if back_angle >= 10:
                            last_feedback = "Try to keep your back straighter"
                            form_status = "warning"
                        elif abs(shoulder_height - hip_height) >= 0.1:
                            last_feedback = "Keep your shoulders and hips aligned"
                            form_status = "warning"
                        elif abs(hip_height - knee_height) >= 0.1:
                            last_feedback = "Keep your hips level"
                            form_status = "warning"
                        else:
                            last_feedback = "Keep going, maintain control"
                            form_status = "warning"

                    # Update count based on duration
                    if pose_start_time is not None:
                        elapsed_time = current_time - pose_start_time
                        if elapsed_time >= max_plank_duration:
                            total_pose_time = max_plank_duration
                            return {"count": total_pose_time, "feedback": "Great job! You've completed your plank!"}
                        else:
                            total_pose_time = int(elapsed_time)
                            remaining_time = target_duration - total_pose_time
                            if remaining_time > 0:
                                last_feedback = f"Hold for {remaining_time} more seconds"
                            else:
                                last_feedback = "Excellent! Keep holding for extra credit!"
                else:
                    pose_start_time = None
                    last_feedback = "Cannot detect body position. Please ensure you're visible in the camera"
                    form_status = "warning"

                # Add a small delay to prevent high CPU usage
                time.sleep(0.1)

            # If we hit the timeout
            if total_pose_time > 0:
                return {"count": total_pose_time, "feedback": f"Time's up! You held the plank for {total_pose_time} seconds. {last_feedback}"}
            else:
                return {"count": 0, "feedback": "No plank detected. Please ensure you're visible in the camera"}

        except Exception as e:
            logger.error(f"Error during plank detection: {str(e)}")
            return {"count": total_pose_time, "feedback": f"Error: {str(e)}"}
        finally:
            pose.close()

if __name__ == "__main__":
    result = count_exercise()
    print(result) 