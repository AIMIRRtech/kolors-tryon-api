const healthText = document.getElementById("healthText");
const runText = document.getElementById("runText");
const tryonForm = document.getElementById("tryonForm");
const sampleBtn = document.getElementById("sampleBtn");
const submitBtn = document.getElementById("submitBtn");
const personUrlInput = document.getElementById("personUrl");
const garmentUrlInput = document.getElementById("garmentUrl");
const seedInput = document.getElementById("seed");
const randomizeInput = document.getElementById("randomize");
const personPreview = document.getElementById("personPreview");
const garmentPreview = document.getElementById("garmentPreview");
const resultImage = document.getElementById("resultImage");
const resultMeta = document.getElementById("resultMeta");

const SAMPLE_PERSON = "https://pub-582b7213209642b9b995c96c95a30381.r2.dev/vt_human.jpg";
const SAMPLE_GARMENT = "https://pub-582b7213209642b9b995c96c95a30381.r2.dev/vt_top.jpeg";

function setPreview(imgEl, value) {
  imgEl.src = value || "";
  imgEl.style.visibility = value ? "visible" : "hidden";
}

async function checkHealth() {
  healthText.textContent = "Checking...";
  try {
    const res = await fetch("/api/health");
    const data = await res.json();
    healthText.textContent = `${res.status} ${data.status || "unknown"} (v${data.version || "?"})`;
  } catch (error) {
    healthText.textContent = `error: ${error.message}`;
  }
}

function useSample() {
  personUrlInput.value = SAMPLE_PERSON;
  garmentUrlInput.value = SAMPLE_GARMENT;
  setPreview(personPreview, SAMPLE_PERSON);
  setPreview(garmentPreview, SAMPLE_GARMENT);
  runText.textContent = "Sample data loaded";
}

function getPayload() {
  return {
    person_image_url: personUrlInput.value.trim(),
    garment_image_url: garmentUrlInput.value.trim(),
    seed: Number(seedInput.value || 0),
    randomize_seed: Boolean(randomizeInput.checked),
  };
}

tryonForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const payload = getPayload();
  setPreview(personPreview, payload.person_image_url);
  setPreview(garmentPreview, payload.garment_image_url);

  submitBtn.disabled = true;
  runText.textContent = "Submitting request to /api/tryon...";
  resultMeta.textContent = "Working... this may take up to 60-120 seconds.";

  try {
    const res = await fetch("/api/tryon", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await res.json();

    if (!res.ok || !data.success) {
      runText.textContent = `Failed (${res.status})`;
      resultMeta.textContent = data.message || "Unknown error";
      resultImage.removeAttribute("src");
      return;
    }

    const resultSrc = data.result_image_base64
      ? `data:image/png;base64,${data.result_image_base64}`
      : data.result_image_url;

    if (resultSrc) {
      resultImage.src = resultSrc;
    }

    runText.textContent = "Completed successfully";
    resultMeta.textContent = `seed=${data.seed_used} | url=${data.result_image_url || "n/a"}`;
  } catch (error) {
    runText.textContent = "Failed (network)";
    resultMeta.textContent = error.message;
    resultImage.removeAttribute("src");
  } finally {
    submitBtn.disabled = false;
  }
});

sampleBtn.addEventListener("click", useSample);
personUrlInput.addEventListener("input", () => setPreview(personPreview, personUrlInput.value.trim()));
garmentUrlInput.addEventListener("input", () => setPreview(garmentPreview, garmentUrlInput.value.trim()));

setPreview(personPreview, "");
setPreview(garmentPreview, "");
checkHealth();
