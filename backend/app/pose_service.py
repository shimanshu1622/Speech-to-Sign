# import os
# import subprocess

# PROJECT_ROOT = os.path.abspath(
#     os.path.join(os.path.dirname(__file__), "../../")
# )

# WORDS_DIR = os.path.join(PROJECT_ROOT, "asl_videos", "words")
# POSES_DIR = os.path.join(PROJECT_ROOT, "asl_videos", "poses")

# os.makedirs(POSES_DIR, exist_ok=True)

# CONTAINER_NAME = "genasl-container"


# def extract_pose_for_gloss(gloss: str):
#     video = os.path.join(WORDS_DIR, f"{gloss}.mp4")
#     pose = os.path.join(POSES_DIR, f"{gloss}.npy")

#     if not os.path.exists(video):
#         raise FileNotFoundError(f"Missing ASL clip: {video}")

#     if os.path.exists(pose):
#         return pose  # cached

#     cmd = [
#         "docker", "exec", CONTAINER_NAME,
#         "python3", "/workspace/docker/rtmo/extract_pose.py",
#         f"/workspace/asl_videos/words/{gloss}.mp4",
#         f"/workspace/asl_videos/poses/{gloss}.npy",
#     ]

#     subprocess.run(cmd, check=True)
#     return pose
