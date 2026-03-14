import os

WORDS_DIR = r"C:\Projects\STS MVP\asl_videos\words"

def main():
    renamed = 0
    skipped = 0

    for fname in os.listdir(WORDS_DIR):
        if not fname.lower().endswith(".mp4"):
            continue

        if not fname.startswith("#"):
            skipped += 1
            continue

        old_path = os.path.join(WORDS_DIR, fname)

        new_name = "HASH-" + fname[1:]
        new_path = os.path.join(WORDS_DIR, new_name)

        if os.path.exists(new_path):
            print(f"⚠️  Skipping (already exists): {new_name}")
            skipped += 1
            continue

        os.rename(old_path, new_path)
        print(f"✅ Renamed: {fname} → {new_name}")
        renamed += 1

    print("\n--- Summary ---")
    print(f"Renamed: {renamed}")
    print(f"Skipped: {skipped}")

if __name__ == "__main__":
    main()
