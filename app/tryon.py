import asyncio
import base64
import io
import os
import tempfile

import httpx
from PIL import Image
from gradio_client import Client, handle_file

from app.config import HF_SPACE_URL, HF_TOKEN

_client = None


def get_client():
    global _client
    if _client is None:
        _client = Client(HF_SPACE_URL, hf_token=HF_TOKEN)
    return _client


async def download_image(url: str) -> str:
    """Download image from URL and save to temp file, return path."""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url)
        resp.raise_for_status()
    img = Image.open(io.BytesIO(resp.content)).convert("RGB")
    tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
    img.save(tmp.name, "JPEG", quality=95)
    return tmp.name


def image_to_base64(filepath: str) -> str:
    with open(filepath, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


async def run_tryon(
    person_image_url: str,
    garment_image_url: str,
    seed: int = 0,
    randomize_seed: bool = True,
) -> dict:
    """Run virtual try-on via HuggingFace Space API."""
    person_path = await download_image(person_image_url)
    garment_path = await download_image(garment_image_url)

    loop = asyncio.get_event_loop()
    client = get_client()

    try:
        result = await loop.run_in_executor(
            None,
            lambda: client.predict(
                person_img=handle_file(person_path),
                garment_img=handle_file(garment_path),
                seed=seed,
                randomize_seed=randomize_seed,
                api_name="/tryon",
            ),
        )

        result_image_path, seed_used, info = result

        if result_image_path and info == "Success":
            result_b64 = image_to_base64(result_image_path)
            return {
                "success": True,
                "result_image_base64": result_b64,
                "seed_used": seed_used,
                "message": "Success",
            }
        else:
            return {
                "success": False,
                "result_image_base64": None,
                "seed_used": seed_used,
                "message": info or "Try-on failed",
            }
    finally:
        for p in [person_path, garment_path]:
            try:
                os.unlink(p)
            except OSError:
                pass


async def run_tryon_from_files(
    person_path: str,
    garment_path: str,
    seed: int = 0,
    randomize_seed: bool = True,
) -> dict:
    """Run virtual try-on from local file paths."""
    loop = asyncio.get_event_loop()
    client = get_client()

    try:
        result = await loop.run_in_executor(
            None,
            lambda: client.predict(
                person_img=handle_file(person_path),
                garment_img=handle_file(garment_path),
                seed=seed,
                randomize_seed=randomize_seed,
                api_name="/tryon",
            ),
        )

        result_image_path, seed_used, info = result

        if result_image_path and info == "Success":
            result_b64 = image_to_base64(result_image_path)
            return {
                "success": True,
                "result_image_base64": result_b64,
                "seed_used": seed_used,
                "message": "Success",
            }
        else:
            return {
                "success": False,
                "result_image_base64": None,
                "seed_used": seed_used,
                "message": info or "Try-on failed",
            }
    except Exception as e:
        return {
            "success": False,
            "result_image_base64": None,
            "seed_used": None,
            "message": str(e),
        }
