import sys
from pathlib import Path
import subprocess

WORDS_DIR = Path("asl_videos/words")
POSES_DIR = Path("asl_videos/poses")

POSES_DIR.mkdir(parents=True, exist_ok=True)


def main():
    if not WORDS_DIR.exists():
        raise RuntimeError(f"Missing directory: {WORDS_DIR}")

    videos = sorted(WORDS_DIR.glob("*.mp4"))

    if not videos:
        print("No videos found.")
        return

    print(f"Found {len(videos)} videos")

    extracted = 0
    skipped = 0
    failed = 0

    for video in videos:
        out = POSES_DIR / f"{video.stem}.npy"

        if out.exists():
            skipped += 1
            continue

        print(f"[+] Extracting {video.name}")

        try:
            subprocess.run(
                [
                    sys.executable,
                    "extract_pose.py",
                    str(video),
                    str(out),
                ],
                check=True,
            )
            extracted += 1
        except subprocess.CalledProcessError as e:
            print(f"[!] Failed: {video.name}")
            failed += 1

    print("\nDone")
    print(f"Extracted: {extracted}")
    print(f"Skipped:   {skipped}")
    print(f"Failed:    {failed}")


if __name__ == "__main__":
    main()
