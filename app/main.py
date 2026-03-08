import asyncio
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from app.config import API_KEY
from app.tryon import run_tryon

app = FastAPI(title='Kolors Virtual Try-On API', version='2.0.0')
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])

def verify_api_key(x_api_key=None):
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail='Invalid API key')

class TryOnRequest(BaseModel):
    person_image_url: str
    garment_image_url: str
    seed: int = 0
    randomize_seed: bool = True

class BatchTryOnRequest(BaseModel):
    person_image_url: str
    garment_image_urls: List[str]
    seed: int = 0
    randomize_seed: bool = True

@app.get('/health')
async def health():
    return {'status': 'ok', 'version': '2.0.0'}

@app.post('/tryon')
async def tryon_endpoint(req: TryOnRequest, x_api_key: str = Header(None)):
    verify_api_key(x_api_key)
    return await run_tryon(req.person_image_url, req.garment_image_url, req.seed, req.randomize_seed)

@app.post('/tryon/batch')
async def batch_tryon(req: BatchTryOnRequest, x_api_key: str = Header(None)):
    verify_api_key(x_api_key)
    if len(req.garment_image_urls) > 4:
        raise HTTPException(status_code=400, detail='Max 4 garments')
    tasks = [run_tryon(req.person_image_url, u, req.seed, req.randomize_seed) for u in req.garment_image_urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return {'results': [r if not isinstance(r, Exception) else {'success': False, 'message': str(r)} for r in results]}