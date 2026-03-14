import cv2
import numpy as np
import sys
from pathlib import Path
import mediapipe as mp

from mediapipe.python.solutions.face_mesh import FaceMesh


def extract_head(video_path: str, output_path: str):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path}")

    face_mesh = FaceMesh(
        static_image_mode=False,
        refine_landmarks=False,
        max_num_faces=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    head_frames = []

    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            break

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = face_mesh.process(rgb)

        # Default: neutral head
        yaw, pitch, roll = 0.0, 0.0, 0.0

        if res.multi_face_landmarks:
            lm = res.multi_face_landmarks[0].landmark

            # Stable reference points
            nose = np.array([lm[1].x, lm[1].y, lm[1].z])
            left_eye = np.array([lm[33].x, lm[33].y, lm[33].z])
            right_eye = np.array([lm[263].x, lm[263].y, lm[263].z])
            chin = np.array([lm[152].x, lm[152].y, lm[152].z])

            # Vectors
            eye_vec = right_eye - left_eye
            nose_vec = chin - nose

            # Normalize safely
            if np.linalg.norm(eye_vec) > 1e-6:
                eye_vec /= np.linalg.norm(eye_vec)
            if np.linalg.norm(nose_vec) > 1e-6:
                nose_vec /= np.linalg.norm(nose_vec)

            # Angles (radians)
            yaw = np.arctan2(eye_vec[2], eye_vec[0])
            pitch = np.arctan2(nose_vec[1], nose_vec[2])
            roll = np.arctan2(eye_vec[1], eye_vec[0])

        head_frames.append([yaw, pitch, roll])

    cap.release()

    head_array = np.asarray(head_frames, dtype=np.float32)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    np.save(output_path, head_array)

    print(f"Saved head motion: {head_array.shape} → {output_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python extract_head.py <input.mp4> <output.npy>")
        sys.exit(1)

    extract_head(sys.argv[1], sys.argv[2])
