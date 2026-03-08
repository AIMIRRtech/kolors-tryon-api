import express from "express";
import dotenv from "dotenv";
import path from "path";
import { fileURLToPath } from "url";

dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const publicDir = path.join(__dirname, "public");

const app = express();
app.use(express.json({ limit: "2mb" }));
app.use(express.static(publicDir));

const PORT = Number(process.env.PORT || 3000);
const API_BASE_URL = (process.env.API_BASE_URL || "http://localhost:8000").replace(/\/$/, "");
const API_KEY = process.env.API_KEY || "";

async function fetchWithTimeout(url, options = {}, timeoutMs = 310000) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, { ...options, signal: controller.signal });
  } finally {
    clearTimeout(timeout);
  }
}

app.get("/api/health", async (_req, res) => {
  try {
    const upstream = await fetchWithTimeout(`${API_BASE_URL}/health`, {}, 10000);
    const payload = await upstream.json();
    return res.status(upstream.status).json(payload);
  } catch (error) {
    return res.status(502).json({
      status: "error",
      message: "Could not reach backend health endpoint",
      detail: String(error?.message || error),
    });
  }
});

app.post("/api/tryon", async (req, res) => {
  const { person_image_url, garment_image_url, seed = 0, randomize_seed = true } = req.body || {};

  if (!person_image_url || !garment_image_url) {
    return res.status(400).json({
      success: false,
      message: "person_image_url and garment_image_url are required",
    });
  }

  try {
    const upstream = await fetchWithTimeout(
      `${API_BASE_URL}/tryon`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(API_KEY ? { "X-API-Key": API_KEY } : {}),
        },
        body: JSON.stringify({
          person_image_url,
          garment_image_url,
          seed,
          randomize_seed,
        }),
      },
      320000,
    );

    const text = await upstream.text();
    let payload;
    try {
      payload = JSON.parse(text);
    } catch {
      payload = {
        success: false,
        message: "Upstream returned non-JSON response",
        raw: text,
      };
    }

    return res.status(upstream.status).json(payload);
  } catch (error) {
    const isTimeout = String(error?.name || "") === "AbortError";
    return res.status(isTimeout ? 504 : 502).json({
      success: false,
      message: isTimeout ? "Request to backend timed out" : "Failed to call backend /tryon",
      detail: String(error?.message || error),
    });
  }
});

app.get("*", (_req, res) => {
  res.sendFile(path.join(publicDir, "index.html"));
});

app.listen(PORT, () => {
  console.log(`Demo UI running on http://localhost:${PORT}`);
  console.log(`Proxying backend at ${API_BASE_URL}`);
});
