import asyncio
import os
import tempfile
from typing import Optional

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware

from app.models import TryOnRequest, TryOnResponse, BatchTryOnRequest
from app.tryon import run_tryon, run_tryon_from_files, image_to_base64
from app.config import API_KEY

app = FastAPI(
    title="Kolors Virtual Try-On API",
    description="Upload a person image + garment image to get a try-on result. Built for Shopify integration.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def verify_api_key(x_api_key: Optional[str] = Header(None)):
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/tryon", response_model=TryOnResponse)
async def tryon_from_urls(request: TryOnRequest, _=Depends(verify_api_key)):
    """
    Virtual try-on from image URLs.
    Pass person_image_url and garment_image_url (e.g. Shopify CDN URLs).
    """
    if not request.person_image_url or not request.garment_image_url:
        raise HTTPException(
            status_code=400,
            detail="Both person_image_url and garment_image_url required",
        )
    try:
        result = await run_tryon(
            person_image_url=request.person_image_url,
            garment_image_url=request.garment_image_url,
            seed=request.seed,
            randomize_seed=request.randomize_seed,
        )
        return TryOnResponse(**result)
    except Exception as e:
        return TryOnResponse(success=False, message=str(e))


@app.post("/tryon/upload", response_model=TryOnResponse)
async def tryon_from_upload(
    person_image: UploadFile = File(...),
    garment_image: UploadFile = File(...),
    _=Depends(verify_api_key),
):
    """Virtual try-on from direct file uploads."""
    person_bytes = await person_image.read()
    garment_bytes = await garment_image.read()

    person_tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
    person_tmp.write(person_bytes)
    person_tmp.close()

    garment_tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
    garment_tmp.write(garment_bytes)
    garment_tmp.close()

    try:
        result = await run_tryon_from_files(
            person_path=person_tmp.name,
            garment_path=garment_tmp.name,
        )
        return TryOnResponse(**result)
    finally:
        os.unlink(person_tmp.name)
        os.unlink(garment_tmp.name)


@app.post("/tryon/batch")
async def tryon_batch(request: BatchTryOnRequest, _=Depends(verify_api_key)):
    """
    Try on multiple garments (up to 4) on the same person.
    Perfect for Shopify: pass 1 person image + up to 4 garment URLs.
    """
    if len(request.garment_image_urls) > 4:
        raise HTTPException(
            status_code=400, detail="Maximum 4 garments per batch"
        )

    tasks = [
        run_tryon(
            person_image_url=request.person_image_url,
            garment_image_url=garment_url,
            seed=request.seed,
            randomize_seed=request.randomize_seed,
        )
        for garment_url in request.garment_image_urls
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    output = []
    for i, r in enumerate(results):
        if isinstance(r, Exception):
            output.append({"garment_index": i, "success": False, "message": str(r)})
        else:
            output.append({"garment_index": i, **r})

    return {"results": output}
