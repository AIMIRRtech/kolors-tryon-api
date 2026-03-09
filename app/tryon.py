import asyncio
import base64
import io
import os
import tempfile
import httpx
import json
from PIL import Image
from app.config import HF_TOKEN

FAL_KEY = os.getenv("FAL_KEY", "")
FAL_MODEL = "fal-ai/kling/v1-5/kolors-virtual-try-on"


def decode_data_uri(data_uri: str) -> bytes:
    """Decode a data URI to raw bytes"""
    # Format: data:image/jpeg;base64,/9j/4AAQ...
    header, b64_data = data_uri.split(",", 1)
    return base64.b64decode(b64_data)


async def download_image(url: str) -> str:
    """Download image from URL (or decode data URI) and save to temp file, return path"""
    if url.startswith("data:"):
        img_bytes = decode_data_uri(url)
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    else:
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


def image_url_to_data_uri(filepath: str) -> str:
    b64 = image_to_base64(filepath)
    return f"data:image/jpeg;base64,{b64}"


async def run_tryon(
    person_image_url: str,
    garment_image_url: str,
    seed: int = 0,
    randomize_seed: bool = True,
) -> dict:
    """Run virtual try-on using fal.ai Kling Kolors VTON endpoint"""
    person_path = await download_image(person_image_url)
    garment_path = await download_image(garment_image_url)

    # Convert to data URIs for fal.ai if they were uploaded files
    person_data_uri = image_url_to_data_uri(person_path)
    garment_data_uri = image_url_to_data_uri(garment_path)

    # Use original URLs if they are real URLs, data URIs for uploaded files
    fal_person_url = person_image_url if not person_image_url.startswith("data:") else person_data_uri
    fal_garment_url = garment_image_url if not garment_image_url.startswith("data:") else garment_data_uri

    try:
        # Use fal.ai API
        async with httpx.AsyncClient(timeout=120) as client:
            # Submit the request
            submit_resp = await client.post(
                f"https://queue.fal.run/{FAL_MODEL}",
                headers={
                    "Authorization": f"Key {FAL_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "human_image_url": fal_person_url,
                    "garment_image_url": fal_garment_url,
                },
            )
            submit_resp.raise_for_status()
            submit_data = submit_resp.json()
            request_id = submit_data.get("request_id")
            status_url = submit_data.get("status_url")
            response_url = submit_data.get("response_url")

            if not status_url or not response_url:
                return {
                    "success": False,
                    "result_image_base64": None,
                    "seed_used": seed,
                    "message": f"Missing fal queue URLs in submit response: {submit_data}",
                }

            # Poll for result
            for _ in range(60):
                status_resp = await client.get(
                    status_url,
                    headers={"Authorization": f"Key {FAL_KEY}"},
                )
                status_data = status_resp.json()
                if status_data.get("status") == "COMPLETED":
                    break
                elif status_data.get("status") == "FAILED":
                    return {
                        "success": False,
                        "result_image_base64": None,
                        "seed_used": seed,
                        "message": f"Failed: {status_data}",
                    }
                await asyncio.sleep(2)

            # Get result
            result_resp = await client.get(
                response_url,
                headers={"Authorization": f"Key {FAL_KEY}"},
            )
            result_resp.raise_for_status()
            result_data = result_resp.json()

            # Download result image
            result_image_url = result_data.get("image", {}).get("url", "")
            if result_image_url:
                img_resp = await client.get(result_image_url)
                result_b64 = base64.b64encode(img_resp.content).decode("utf-8")
                return {
                    "success": True,
                    "result_image_base64": result_b64,
                    "result_image_url": result_image_url,
                    "seed_used": seed,
                    "message": "Success",
                }
            else:
                return {
                    "success": False,
                    "result_image_base64": None,
                    "seed_used": seed,
                    "message": f"No image URL in response: {result_data}",
                }
    except Exception as e:
        return {
            "success": False,
            "result_image_base64": None,
            "seed_used": seed,
            "message": str(e),
        }
    finally:
        for p in [person_path, garment_path]:
            try:
                os.unlink(p)
            except:
                pass
