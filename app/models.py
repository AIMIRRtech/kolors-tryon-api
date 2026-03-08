from pydantic import BaseModel
from typing import Optional


class TryOnRequest(BaseModel):
    person_image_url: Optional[str] = None
    garment_image_url: Optional[str] = None
    seed: int = 0
    randomize_seed: bool = True


class TryOnResponse(BaseModel):
    success: bool
    result_image_base64: Optional[str] = None
    seed_used: Optional[int] = None
    message: str = ""


class BatchTryOnRequest(BaseModel):
    person_image_url: str
    garment_image_urls: list[str]
    seed: int = 0
    randomize_seed: bool = True
