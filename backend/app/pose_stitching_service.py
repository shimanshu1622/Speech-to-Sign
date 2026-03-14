import numpy as np
from pathlib import Path
from typing import List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[2]

POSES_DIR = PROJECT_ROOT / "asl_videos" / "poses"
HEADS_DIR = PROJECT_ROOT / "asl_videos" / "heads"



def stitch_pose_sequences(
    gloss_keys: List[str],
    pause_frames: int = 15 # 15 frames = 0.5s at 30fps
) -> Tuple[np.ndarray, np.ndarray]:
    
    pose_seqs = []
    head_seqs = []

    for key in gloss_keys:
        # Handle the dynamic pause token
        if key == "__PAUSE__":
            # Create empty arrays (zeros) to represent the pause duration
            # Assuming pose shape is (frames, keypoints, dimensions) e.g., (N, 33, 3)
            # You will need to hardcode the exact shape of your ASLLVD .npy files here
            pose_seqs.append(np.zeros((pause_frames, 33, 3))) 
            head_seqs.append(np.zeros((pause_frames, 468, 3)))
            continue

        pose_path = POSES_DIR / f"{key}.npy"
        head_path = HEADS_DIR / f"{key}.npy"

        # Align with video service: safely skip missing files to prevent desync
        if not pose_path.exists() or not head_path.exists():
            print(f"Warning: Missing pose/head data for {key}. Skipping.")
            continue

        poses = np.load(pose_path)
        heads = np.load(head_path)

        if poses.shape[0] != heads.shape[0]:
            print(f"Warning: Frame mismatch in {key}. Skipping.")
            continue

        pose_seqs.append(poses)
        head_seqs.append(heads)

    if not pose_seqs:
        raise ValueError("No valid poses found to stitch")

    stitched_pose = np.concatenate(pose_seqs, axis=0)
    stitched_head = np.concatenate(head_seqs, axis=0)

    return stitched_pose, stitched_head