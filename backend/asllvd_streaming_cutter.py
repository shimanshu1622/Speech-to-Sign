import os
import re
import shutil
import subprocess
import tempfile
import pandas as pd
from tqdm import tqdm

# =========================
# CONFIG
# =========================

CSV_PATH = "../asllvd_metadata/asllvd_signs_2024_06_27.csv"
ASLLVD_RAW_DIR = "../asllvd_raw"
OUTPUT_DIR = "../asl_videos/words"
TMP_DIR = tempfile.gettempdir()

TARGET_FPS = 25
TARGET_RES = (1280, 720)

os.makedirs(OUTPUT_DIR, exist_ok=True)

# =========================
# CSV COLUMNS
# =========================

COL_GLOSS_MAIN = "main entry gloss label"
COL_GLOSS_VARIANT = "entry/variant gloss label"
COL_START_FRAME = "start frame of the sign (relative to full videos)"
COL_END_FRAME = "end frame of the sign (relative to full videos)"
COL_VIDEO_FILE = "full video file"

# =========================
# GLOSS NORMALIZATION
# =========================

def canonicalize_gloss(text: str) -> str:
    """
    Linguistic canonical form (spaces, metadata removed).
    Preserves # for loan signs.
    """
    text = text.upper()

    # Remove parenthesized metadata
    text = re.sub(r"\([^)]*\)", "", text)

    # Remove repetition markers
    text = text.replace("++", "")
    text = text.replace("+", " ")

    # Replace lexical alternatives
    text = text.replace("/", " ")

    # Remove numeric suffixes (_2, _3)
    text = re.sub(r"_\d+", "", text)

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def gloss_to_key(gloss: str) -> str:
    """
    Filesystem / API safe key.
    - spaces -> hyphens
    - #AC -> HASH-AC
    """
    key = gloss.replace(" ", "-")
    if key.startswith("#"):
        key = "HASH-" + key[1:]
    return key

# =========================
# VIDEO HELPERS
# =========================

def find_available_videos():
    videos = {}
    for root, _, files in os.walk(ASLLVD_RAW_DIR):
        for f in files:
            if f.lower().endswith((".mov", ".mp4", ".avi")):
                videos[f] = os.path.join(root, f)
    return videos


def get_video_fps(video_path):
    cmd = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=r_frame_rate",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path
    ]
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    rate = result.stdout.strip()
    if not rate:
        return None

    if "/" in rate:
        num, den = rate.split("/")
        return float(num) / float(den)

    return float(rate)


def extract_clip(video_path, start_frame, end_frame, out_path):
    fps = get_video_fps(video_path)
    if not fps or fps <= 0:
        return False

    start_sec = start_frame / fps
    end_sec = end_frame / fps

    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start_sec),
        "-to", str(end_sec),
        "-i", video_path,
        "-vf", f"scale={TARGET_RES[0]}:{TARGET_RES[1]}",
        "-r", str(TARGET_FPS),
        "-an",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        out_path
    ]

    result = subprocess.run(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    return result.returncode == 0 and os.path.exists(out_path)


def score_clip(video_path):
    """
    Deterministic, fast quality proxy.
    """
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path
    ]
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    try:
        duration = float(result.stdout.strip())
    except:
        return 0.0

    # Prefer ~1–1.5s signs
    duration_score = max(0.0, 1.0 - abs(duration - 1.2))

    # Motion proxy via file size
    size_mb = os.path.getsize(video_path) / (1024 * 1024)
    motion_score = min(size_mb / 2.0, 1.0)

    return 0.6 * duration_score + 0.4 * motion_score

# =========================
# MAIN
# =========================

def main():
    df = pd.read_csv(CSV_PATH)
    available_videos = find_available_videos()

    print(f"📂 Found {len(available_videos)} available source videos")

    # -------------------------
    # Bootstrap best scores
    # -------------------------
    best_scores = {}
    for fname in os.listdir(OUTPUT_DIR):
        if not fname.lower().endswith(".mp4"):
            continue
        gloss_key = os.path.splitext(fname)[0]
        clip_path = os.path.join(OUTPUT_DIR, fname)
        best_scores[gloss_key] = score_clip(clip_path)

    # -------------------------
    # Stream CSV
    # -------------------------
    for _, row in tqdm(df.iterrows(), total=len(df)):
        video_name = row[COL_VIDEO_FILE]
        if video_name not in available_videos:
            continue

        gloss_raw = row[COL_GLOSS_MAIN] or row[COL_GLOSS_VARIANT]
        if not isinstance(gloss_raw, str):
            continue

        canonical_gloss = canonicalize_gloss(gloss_raw)
        if not canonical_gloss:
            continue

        gloss_key = gloss_to_key(canonical_gloss)

        try:
            start_f = int(row[COL_START_FRAME])
            end_f = int(row[COL_END_FRAME])
        except:
            continue

        src_video = available_videos[video_name]
        tmp_clip = os.path.join(TMP_DIR, f"tmp_{gloss_key}.mp4")

        if not extract_clip(src_video, start_f, end_f, tmp_clip):
            continue

        score = score_clip(tmp_clip)
        final_clip = os.path.join(OUTPUT_DIR, f"{gloss_key}.mp4")

        if gloss_key not in best_scores:
            shutil.move(tmp_clip, final_clip)
            best_scores[gloss_key] = score
        else:
            if score > best_scores[gloss_key]:
                os.remove(final_clip)
                shutil.move(tmp_clip, final_clip)
                best_scores[gloss_key] = score
            else:
                os.remove(tmp_clip)

    print("✅ Streaming ASLLVD extraction complete.")

if __name__ == "__main__":
    main()
