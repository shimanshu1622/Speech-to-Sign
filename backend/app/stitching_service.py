import os
import subprocess
import tempfile
from typing import List

# =========================
# CONFIG
# =========================

WORDS_DIR = os.getenv(
    "ASL_WORDS_DIR",
    os.path.abspath("../asl_videos/words")
)

# Reserved non-linguistic control tokens
CONTROL_TOKENS = {"__PAUSE__"}

# Filename used for pause clip
PAUSE_CLIP_NAME = "__PAUSE__.mp4"


# =========================
# CORE STITCHING LOGIC
# =========================

def stitch_gloss_keys(
    tokens: List[str],
    output_path: str
) -> None:
    """
    Stitch a sequence of gloss keys and control tokens into a single MP4.
    Windows-safe implementation.
    """

    if not tokens:
        raise ValueError("No tokens provided for stitching")

    fd, list_path = tempfile.mkstemp(suffix=".txt")
    os.close(fd)  # IMPORTANT: release Windows file lock

    try:
        with open(list_path, "w", encoding="utf-8") as f:
            for token in tokens:
                if token in CONTROL_TOKENS:
                    clip_name = PAUSE_CLIP_NAME
                else:
                    clip_name = f"{token}.mp4"

                clip_path = os.path.abspath(
                    os.path.join(WORDS_DIR, clip_name)
                )

                if not os.path.exists(clip_path):
                    # Missing clips are skipped safely
                    continue

                # FFmpeg concat demuxer format
                f.write(f"file '{clip_path}'\n")

        # Abort cleanly if nothing was written
        with open(list_path, "r", encoding="utf-8") as f:
            if not f.read().strip():
                raise ValueError("No valid ASL clips found to stitch")

        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", list_path,
            # Forcing normalization instead of -c copy
            "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2", 
            "-r", "30",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            # Dropping audio to prevent crashes from missing audio tracks
            "-an", 
            output_path
        ]

        subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )

    finally:
        try:
            os.unlink(list_path)
        except FileNotFoundError:
            pass

# =========================
# OPTIONAL HELPERS
# =========================

def insert_pauses_between_signs(
    gloss_keys: List[str],
    pause_token: str = "__PAUSE__"
) -> List[str]:
    """
    Utility to automatically insert pauses between signs.

    Example:
    ["CHEAT", "WHO"] →
    ["CHEAT", "__PAUSE__", "WHO"]
    """
    if not gloss_keys:
        return []

    result = []
    for i, key in enumerate(gloss_keys):
        result.append(key)
        if i < len(gloss_keys) - 1:
            result.append(pause_token)

    return result
