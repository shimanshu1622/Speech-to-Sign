import numpy as np
import cv2
import sys

# ---------- CONFIG ----------
WIDTH, HEIGHT = 800, 800
FPS = 25
JOINT_RADIUS = 4
BONE_THICKNESS = 2

# ---------- BONE DEFINITIONS ----------

HEAD_BONES = [
    (0, 1), (0, 2),        # nose → eyes
    (1, 3), (2, 4),        # eyes → ears
    (5, 6),                # mouth
    (0, 5), (0, 6),        # nose → mouth
]

BODY_BONES = [
    (7, 8), (8, 9),        # left arm
    (10,11), (11,12),      # right arm
    (7,10),                # shoulders
]

HAND_BONES = [
    (0,1),(1,2),(2,3),(3,4),
    (0,5),(5,6),(6,7),(7,8),
    (0,9),(9,10),(10,11),(11,12),
    (0,13),(13,14),(14,15),(15,16),
    (0,17),(17,18),(18,19),(19,20),
]

# ---------- DRAW FUNCTION ----------

def draw_skeleton(pose):
    img = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)

    def to_px(pt):
        return int(pt[0] * WIDTH), int(pt[1] * HEIGHT)

    # ----- HEAD -----
    for a, b in HEAD_BONES:
        cv2.line(img, to_px(pose[a]), to_px(pose[b]), (255, 255, 0), 2)

    # ----- BODY -----
    for a, b in BODY_BONES:
        cv2.line(img, to_px(pose[a]), to_px(pose[b]), (0, 255, 0), 2)

    # ----- HANDS -----
    for base in (13, 34):
        for a, b in HAND_BONES:
            cv2.line(
                img,
                to_px(pose[base + a]),
                to_px(pose[base + b]),
                (255, 255, 255),
                1
            )

    # ----- JOINTS -----
    for i, joint in enumerate(pose):
        if i < 7:
            color = (255, 255, 0)      # head
        elif i < 13:
            color = (0, 255, 0)        # body
        else:
            color = (255, 0, 0)        # hands

        cv2.circle(img, to_px(joint), JOINT_RADIUS, color, -1)

    cv2.imshow("Skeleton Preview", img)


# ---------- MAIN ----------

def main(path):
    poses = np.load(path)
    print("Loaded pose array:", poses.shape)

    delay = int(1000 / FPS)

    for pose in poses:
        draw_skeleton(pose)
        if cv2.waitKey(delay) & 0xFF == 27:
            break

    cv2.destroyAllWindows()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python preview_pose.py <pose.npy>")
        sys.exit(1)

    main(sys.argv[1])
