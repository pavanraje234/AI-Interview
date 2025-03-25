import cv2
import mediapipe as mp
import numpy as np

# Initialize Mediapipe solutions
mp_pose = mp.solutions.pose
mp_face_mesh = mp.solutions.face_mesh

def analyze_posture_and_eyes():
    """
    Analyzes posture and eye contact using the webcam feed.
    Returns posture_score and eye_score (out of 10).
    """
    # Initialize Mediapipe Pose and Face Mesh
    pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
    face_mesh = mp_face_mesh.FaceMesh(min_detection_confidence=0.5, min_tracking_confidence=0.5)

    # Initialize video capture
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return 0, 0  # Return default scores if the camera fails to open

    posture_score = 0
    eye_score = 0
    frame_count = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame from camera.")
            break

        frame_count += 1
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Process frame for posture analysis
        pose_results = pose.process(rgb_frame)
        if pose_results.pose_landmarks:
            landmarks = pose_results.pose_landmarks.landmark
            # Example: Check if shoulders are level
            left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
            right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
            if abs(left_shoulder.y - right_shoulder.y) < 0.05:
                posture_score += 1

        # Process frame for eye analysis
        face_results = face_mesh.process(rgb_frame)
        if face_results.multi_face_landmarks:
            for face_landmarks in face_results.multi_face_landmarks:
                # Example: Check if eyes are looking at the screen
                left_eye = face_landmarks.landmark[33]
                right_eye = face_landmarks.landmark[263]
                if left_eye.x > 0.3 and left_eye.x < 0.7 and right_eye.x > 0.3 and right_eye.x < 0.7:
                    eye_score += 1

        # Display the frame (for debugging purposes)
        cv2.imshow("Posture and Eye Analysis", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        # Stop after analyzing 100 frames
        if frame_count >= 100:
            break

    # Release resources
    cap.release()
    cv2.destroyAllWindows()

    # Calculate final scores
    posture_score = (posture_score / frame_count) * 10
    eye_score = (eye_score / frame_count) * 10

    return posture_score, eye_score