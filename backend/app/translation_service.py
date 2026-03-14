import asyncio
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.job_manager import create_job, run_generate_job, get_job, JobStatus
from app.minio_service import upload_and_get_url

router = APIRouter()

class TranslationRequest(BaseModel):
    text: str

@router.post("/api/translate")
async def translate_text_to_asl(request: TranslationRequest):
    """
    Takes English text, generates the ASL video, and returns the cloud URL.
    """
    job = create_job()
    
    # Define where the temporary file should be stored before upload
    output_path = os.path.abspath(f"temp_{job.id}.mp4")

    try:
        # Run the heavy generation job in a background thread so it doesn't 
        # block the FastAPI event loop for other users.
        await asyncio.to_thread(
            run_generate_job,
            job_id=job.id,
            text=request.text,
            output_path=output_path,
            upload_fn=upload_and_get_url
        )

        # Check the final status
        updated_job = get_job(job.id)
        if updated_job.status == JobStatus.FAILED:
            raise HTTPException(status_code=500, detail=str(updated_job.error))

        return {
            "job_id": job.id,
            "status": "success",
            "video_url": updated_job.result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))