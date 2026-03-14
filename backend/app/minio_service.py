import os
from datetime import timedelta
from minio import Minio
from minio.error import S3Error

# =========================
# CONFIG
# =========================

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"

BUCKET = os.getenv("MINIO_BUCKET", "genasl-videos")

if not MINIO_ENDPOINT:
    raise RuntimeError("MINIO_ENDPOINT not set")


# =========================
# CLIENT
# =========================

client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=MINIO_SECURE,
)


# =========================
# BUCKET HELPERS
# =========================

def ensure_bucket():
    """
    Create bucket if it does not exist.
    Safe to call multiple times.
    """
    found = client.bucket_exists(BUCKET)
    if not found:
        client.make_bucket(BUCKET)


# =========================
# UPLOAD + URL
# =========================

def upload_and_get_url(
    local_path: str,
    object_name: str,
    expiry_minutes: int = 10
) -> str:
    """
    Upload a file and return a presigned GET URL.
    """

    ensure_bucket()

    client.fput_object(
        bucket_name=BUCKET,
        object_name=object_name,
        file_path=local_path,
        content_type="video/mp4"
    )

    url = client.presigned_get_object(
        bucket_name=BUCKET,
        object_name=object_name,
        expires=timedelta(minutes=expiry_minutes)
    )

    return url
