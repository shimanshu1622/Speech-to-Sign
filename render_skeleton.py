import os
import cv2
import numpy as np
import sys
from pathlib import Path
import subprocess

# =========================
# CONFIG
# =========================

WIDTH = 640
HEIGHT = 480
FPS = 25

# Colors (BGR)
COLOR_BODY = (0, 255, 0)
COLOR_HAND = (0, 200, 255)
COLOR_HEAD = (255, 0, 0)

# =========================
# SKELETON TOPOLOGY
# =========================

# Body joints (based on your extractor order)
BODY_EDGES = [
    (0, 1),  # L shoulder → L elbow
    (1, 2),  # L elbow → L wrist
    (3, 4),  # R shoulder → R elbow
    (4, 5),  # R elbow → R wrist
    (0, 3),  # shoulders
]

# MediaPipe hand skeleton
HAND_EDGES = [
    (0, 1), (1, 2), (2, 3), (3, 4),        # thumb
    (0, 5), (5, 6), (6, 7), (7, 8),        # index
    (0, 9), (9,10), (10,11), (11,12),      # middle
    (0,13), (13,14), (14,15), (15,16),     # ring
    (0,17), (17,18), (18,19), (19,20),     # pinky
]

LEFT_HAND_OFFSET = 6
RIGHT_HAND_OFFSET = 27

# =========================
# DRAW HELPERS
# =========================

def to_px(pt):
    x, y, _ = pt
    return int(x * WIDTH), int(y * HEIGHT)


def draw_edges(img, joints, edges, offset=0, color=(255,255,255)):
    for i, j in edges:
        p1 = joints[i + offset]
        p2 = joints[j + offset]
        if np.any(p1) and np.any(p2):
            cv2.line(img, to_px(p1), to_px(p2), color, 2)


def draw_joints(img, joints, color):
    for x, y, z in joints:
        if x == 0 and y == 0:
            continue
        cv2.circle(img, (int(x * WIDTH), int(y * HEIGHT)), 3, color, -1)


def draw_head(img, joints, head_data):
    """
    head_data = [yaw, pitch, roll]
    """

    yaw, pitch, roll = head_data

    ls = joints[0]  # left shoulder
    rs = joints[3]  # right shoulder

    if not np.any(ls) or not np.any(rs):
        return

    # Head center
    cx = int(((ls[0] + rs[0]) / 2) * WIDTH)
    cy = int(((ls[1] + rs[1]) / 2 - 0.12) * HEIGHT)

    # Shoulder distance → head size
    shoulder_dist = np.linalg.norm(
        np.array(ls[:2]) - np.array(rs[:2])
    )

    head_w = int(shoulder_dist * WIDTH * 0.6)
    head_h = int(head_w * 1.25)

    angle = np.degrees(roll)

    cv2.ellipse(
        img,
        ((cx, cy), (head_w, head_h), angle),
        COLOR_HEAD,
        2
    )




# =========================
# MAIN RENDER
# =========================

def render(pose_path, head_path, out_path):
    poses = np.load(pose_path)
    heads = np.load(head_path)

    assert poses.shape[0] == heads.shape[0], "Frame mismatch"

    # 1. Save to a temporary file first
    temp_out_path = str(out_path).replace(".mp4", "_temp.mp4")
    
    # FIX: Explicit type casting for OpenCV 4.13+ strictness
    fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
    writer = cv2.VideoWriter(
        str(temp_out_path),
        int(fourcc),
        float(FPS),
        (int(WIDTH), int(HEIGHT))
    )

    for t in range(poses.shape[0]):
        frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
        frame = frame.copy()  # ensures contiguous memory

        joints = poses[t]
        head = heads[t]

        # Draw body
        draw_edges(frame, joints, BODY_EDGES, color=COLOR_BODY)
        draw_joints(frame, joints[:6], COLOR_BODY)

        # Left hand
        draw_edges(frame, joints, HAND_EDGES, offset=LEFT_HAND_OFFSET, color=COLOR_HAND)
        draw_joints(frame, joints[LEFT_HAND_OFFSET:LEFT_HAND_OFFSET+21], COLOR_HAND)

        # Right hand
        draw_edges(frame, joints, HAND_EDGES, offset=RIGHT_HAND_OFFSET, color=COLOR_HAND)
        draw_joints(frame, joints[RIGHT_HAND_OFFSET:RIGHT_HAND_OFFSET+21], COLOR_HAND)

        # Head motion - Ensure shape matches [yaw, pitch, roll]
        if head.shape == (3,): 
            draw_head(frame, joints, head)

        writer.write(frame)

    writer.release()
    
    # 2. Convert to Web-Safe H.264 using FFmpeg
    cmd = [
        "ffmpeg", "-y",
        "-i", str(temp_out_path),
        "-c:v", "libx264",       
        "-pix_fmt", "yuv420p",   
        str(out_path)
    ]
    
    subprocess.run(
        cmd, 
        stdout=subprocess.DEVNULL, 
        stderr=subprocess.DEVNULL, 
        check=True
    )

    # 3. Clean up the temporary mp4v file
    if os.path.exists(temp_out_path):
        os.remove(temp_out_path)

    print(f"Saved web-safe skeleton video → {out_path}")
    
if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python render_skeleton.py pose.npy head.npy out.mp4")
        sys.exit(1)

    render(sys.argv[1], sys.argv[2], sys.argv[3])
