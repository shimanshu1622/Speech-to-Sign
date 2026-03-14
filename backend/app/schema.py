from typing import List
from pydantic import BaseModel, Field


class StitchRequest(BaseModel):
    gloss_keys: List[str] = Field(
        ...,
        example=["CHEAT", "WHO", "HASH-AC"]
    )


class StitchResponse(BaseModel):
    output_path: str
