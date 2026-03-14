import cv2
import numpy as np
import mediapipe as mp
import sys
from pathlib import Path

mp_pose = mp.solutions.pose
mp_hands = mp.solutions.hands


def extract_pose(video_path: str, output_path: str):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path}")

    pose = mp_pose.Pose(
        static_image_mode=False,
        model_complexity=1,
        enable_segmentation=False,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=2,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    frames = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        h, w, _ = frame.shape
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        pose_result = pose.process(rgb)
        hands_result = hands.process(rgb)

        joints = []

        #BODY (upper body only)
        if pose_result.pose_landmarks:
            lm = pose_result.pose_landmarks.landmark

            def p(idx):
                return [lm[idx].x, lm[idx].y, lm[idx].z]

            # MediaPipe pose indices
            joints.extend([
                p(mp_pose.PoseLandmark.LEFT_SHOULDER),
                p(mp_pose.PoseLandmark.LEFT_ELBOW),
                p(mp_pose.PoseLandmark.LEFT_WRIST),
                p(mp_pose.PoseLandmark.RIGHT_SHOULDER),
                p(mp_pose.PoseLandmark.RIGHT_ELBOW),
                p(mp_pose.PoseLandmark.RIGHT_WRIST),
            ])
        else:
            joints.extend([[0, 0, 0]] * 6)

        # HANDS
        hand_data = {
            "Left": [[0, 0, 0]] * 21,
            "Right": [[0, 0, 0]] * 21,
        }

        if hands_result.multi_hand_landmarks:
            for hand_lms, handedness in zip(
                hands_result.multi_hand_landmarks,
                hands_result.multi_handedness
            ):
                label = handedness.classification[0].label  # "Left" / "Right"
                coords = [
                    [lm.x, lm.y, lm.z]
                    for lm in hand_lms.landmark
                ]
                hand_data[label] = coords

        joints.extend(hand_data["Left"])
        joints.extend(hand_data["Right"])

        frames.append(joints)

    cap.release()

    pose_array = np.array(frames, dtype=np.float32)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    np.save(output_path, pose_array)

    print(f"Saved pose: {pose_array.shape} → {output_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python extract_pose.py <input.mp4> <output.npy>")
        sys.exit(1)

    extract_pose(sys.argv[1], sys.argv[2])
