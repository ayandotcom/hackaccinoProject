import cv2
import math
import mediapipe as mp
import time

def count_tree_pose():
    # Initialize variables
    tree_pose_count = 0
    start_time = time.time()
    timeout = 60  # 60 seconds timeout
    
    # Initialize MediaPipe Pose
    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
    
    # Initialize camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return "Error: Could not open camera"
    
    try:
        while time.time() - start_time < timeout:
            ret, frame = cap.read()
            if not ret:
                return "Error: Could not read frame from camera"
            
            # Convert the BGR image to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Process the frame and get the pose landmarks
            results = pose.process(rgb_frame)
            
            if results.pose_landmarks:
                # Get landmarks
                landmarks = results.pose_landmarks.landmark
                
                # Get key points
                left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
                right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]
                left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
                right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP]
                left_knee = landmarks[mp_pose.PoseLandmark.LEFT_KNEE]
                right_knee = landmarks[mp_pose.PoseLandmark.RIGHT_KNEE]
                left_ankle = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE]
                right_ankle = landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE]
                
                # Calculate angles
                left_leg_angle = math.degrees(math.atan2(left_knee.y - left_hip.y, left_knee.x - left_hip.x))
                right_leg_angle = math.degrees(math.atan2(right_knee.y - right_hip.y, right_knee.x - right_hip.x))
                
                # Check if in tree pose
                if (abs(left_leg_angle) > 45 and abs(right_leg_angle) < 30) or \
                   (abs(right_leg_angle) > 45 and abs(left_leg_angle) < 30):
                    tree_pose_count += 1
                    time.sleep(1)  # Wait for 1 second to avoid counting the same pose multiple times
                
                # Break if we've counted 10 poses
                if tree_pose_count >= 10:
                    break
            
            # Display the frame
            cv2.imshow('Tree Pose Detection', frame)
            
            # Break the loop if 'q' is pressed
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    
    finally:
        # Release resources
        cap.release()
        cv2.destroyAllWindows()
        pose.close()
    
    return f"Completed {tree_pose_count} tree poses" 