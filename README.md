# Kolors Virtual Try-On API

A FastAPI wrapper around the Kolors Virtual Try-On model for Shopify integration.

**Input:** Image of a person + clothing image(s)  
**Output:** Generated image of the clothing on the person

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/tryon` | Try-on from image URLs (JSON body) |
| POST | `/tryon/upload` | Try-on from file uploads (multipart) |
| POST | `/tryon/batch` | Try up to 4 garments on 1 person |

## Quick Start

```bash
git clone https://github.com/AIMIRRtech/kolors-tryon-api.git
cd kolors-tryon-api
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Then visit http://localhost:8000/docs for the interactive Swagger UI.

## Node.js UX Demo (separate consumer app)

A standalone frontend is available in `demo-ui/` and consumes this API through a small Node/Express proxy.

### Run the demo

```bash
cd demo-ui
cp .env.example .env
npm install
npm run start
```

Open http://localhost:3000.

### Demo env vars

| Variable | Description | Default |
|----------|-------------|----------|
| `PORT` | Demo UI server port | `3000` |
| `API_BASE_URL` | FastAPI backend URL | `http://localhost:8000` |
| `API_KEY` | API key sent by Node proxy to backend | `Its@simple1` |

## Usage Examples

### Single garment (URL mode)
```bash
curl -X POST http://localhost:8000/tryon \
  -H "Content-Type: application/json" \
  -d '{
    "person_image_url": "https://your-cdn.com/model.jpg",
    "garment_image_url": "https://cdn.shopify.com/your-store/garment1.jpg"
  }'
```

### Batch (4 Shopify garments)
```bash
curl -X POST http://localhost:8000/tryon/batch \
  -H "Content-Type: application/json" \
  -d '{
    "person_image_url": "https://your-cdn.com/model.jpg",
    "garment_image_urls": [
      "https://cdn.shopify.com/garment1.jpg",
      "https://cdn.shopify.com/garment2.jpg",
      "https://cdn.shopify.com/garment3.jpg",
      "https://cdn.shopify.com/garment4.jpg"
    ]
  }'
```

### File upload mode
```bash
curl -X POST http://localhost:8000/tryon/upload \
  -F "person_image=@person.jpg" \
  -F "garment_image=@garment.jpg"
```

## Deploy to Heroku

```bash
heroku create your-tryon-api
heroku config:set HF_SPACE_URL=AhmedAlmaghz/Kolors-Virtual-Try-On
heroku config:set API_KEY=your_secret_key
git push heroku main
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|----------|
| `HF_SPACE_URL` | HuggingFace Space ID | `AhmedAlmaghz/Kolors-Virtual-Try-On` |
| `HF_TOKEN` | Optional HF token | None |
| `API_KEY` | Protect your API | None |
| `MAX_CONCURRENT` | Max concurrent requests | 5 |

## Response Format

```json
{
  "success": true,
  "result_image_base64": "/9j/4AAQ...",
  "seed_used": 42,
  "message": "Success"
}
```

Decode `result_image_base64` to get the JPEG try-on result image.

## Architecture

This API uses `gradio_client` to call the running HuggingFace Space as the inference backend, so no GPU is needed on Heroku. The batch endpoint runs garments concurrently for speed.
