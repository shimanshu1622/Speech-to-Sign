import uuid
import traceback
from enum import Enum
from typing import Dict, Optional
import tempfile
import os
import subprocess
import numpy as np
import sys
from pathlib import Path

from app.llm_service import english_to_asl_gloss_intent
from app.canonicalizer import ASLLVDCanonicalizer
from app.stitching_service import stitch_gloss_keys, insert_pauses_between_signs
from app.pose_stitching_service import stitch_pose_sequences

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RENDER_SCRIPT = PROJECT_ROOT / "render_skeleton.py"
# =========================
# JOB MODEL
# =========================

class JobStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    DONE = "DONE"
    FAILED = "FAILED"


class Job:
    def __init__(self):
        self.id = str(uuid.uuid4())
        self.status = JobStatus.PENDING
        self.result: Optional[str] = None
        self.error: Optional[str] = None


# =========================
# IN-MEMORY STORE (MVP)
# =========================

_JOBS: Dict[str, Job] = {}


def create_job() -> Job:
    job = Job()
    _JOBS[job.id] = job
    return job


def get_job(job_id: str) -> Optional[Job]:
    return _JOBS.get(job_id)


# =========================
# CANONICALIZER (LOAD ONCE)
# =========================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASL_WORDS_DIR = os.path.join(BASE_DIR, "..", "asl_videos", "words")
# ASL_WORDS_DIR = r"C:\Projects\STS MVP\asl_videos\words"

# KNOWN_GLOSSES = load_asllvd_glosses(ASL_WORDS_DIR)
CANONICALIZER = ASLLVDCanonicalizer(ASL_WORDS_DIR)


# =========================
# JOB EXECUTION
# =========================

def run_generate_job(job_id: str, text: str, output_path: str, upload_fn):
    job = _JOBS.get(job_id)
    if not job: return

    job.status = JobStatus.RUNNING
    skeleton_path = output_path.replace(".mp4", "_skeleton.mp4")
    pose_f_name = None
    head_f_name = None

    try:
        # 1. LLM & Canonicalization
        intent_tokens = english_to_asl_gloss_intent(text)
        glosses = CANONICALIZER.canonicalize(intent_tokens)
        if not glosses:
            raise ValueError("No renderable ASL glosses found.")

        # 2. Stitch the normal Video
        tokens = insert_pauses_between_signs(glosses)
        stitch_gloss_keys(tokens, output_path)
        video_url = upload_fn(output_path, object_name=f"jobs/{job_id}.mp4")

        # 3. Stitch the Poses and Render Skeleton
        poses, heads = stitch_pose_sequences(glosses) # Use exact canonical glosses
        
        with tempfile.NamedTemporaryFile(suffix=".npy", delete=False) as pose_f, \
             tempfile.NamedTemporaryFile(suffix=".npy", delete=False) as head_f:
            
            pose_f_name = pose_f.name
            head_f_name = head_f.name
            np.save(pose_f_name, poses)
            np.save(head_f_name, heads)

        subprocess.run(
            [
                sys.executable,
                str(RENDER_SCRIPT),
                pose_f_name,
                head_f_name,
                skeleton_path,
            ],
            check=True
        )

        skeleton_url = upload_fn(skeleton_path, object_name=f"jobs/{job_id}_skeleton.mp4")

        # 4. Return BOTH URLs as a dictionary
        job.result = {
            "video": video_url,
            "skeleton": skeleton_url,
            "glosses": glosses,  # Optional: return the canonical glosses for frontend display
        }
        job.status = JobStatus.DONE

    except Exception as e:
        job.status = JobStatus.FAILED
        job.error = str(e)
        print(traceback.format_exc())
        
    finally:
        # Cleanup ALL temporary files to save disk space
        for path in [output_path, skeleton_path, pose_f_name, head_f_name]:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except Exception as cleanup_error:
                    print(f"Failed to delete {path}: {cleanup_error}")