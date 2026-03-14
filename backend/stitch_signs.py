import os
import subprocess
import tempfile

WORDS_DIR = "../asl_videos/words"
OUTPUT_DIR = "../asl_videos/stitched"

os.makedirs(OUTPUT_DIR, exist_ok=True)


def stitch_glosses(gloss_keys, output_name="stitched.mp4"):
    """
    gloss_keys: list of gloss_key strings
    """
    list_file = tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".txt",
        delete=False
    )

    try:
        for key in gloss_keys:
            clip_path = os.path.abspath(
                os.path.join(WORDS_DIR, f"{key}.mp4")
            )

            if not os.path.exists(clip_path):
                raise FileNotFoundError(f"Missing clip: {key}")

            list_file.write(f"file '{clip_path}'\n")

        list_file.close()

        output_path = os.path.join(OUTPUT_DIR, output_name)

        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", list_file.name,
            "-c", "copy",
            output_path
        ]

        subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )

        return output_path

    finally:
        os.unlink(list_file.name)


if __name__ == "__main__":
    demo = [
        "CHEAT",
        "WHO",
        "HASH-AC",
        "GOOD-THANK-YOU-MORNING"
    ]

    out = stitch_glosses(demo, "demo.mp4")
    print(f"✅ Stitched video saved to: {out}")
