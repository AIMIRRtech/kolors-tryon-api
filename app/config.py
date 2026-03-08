import os
from dotenv import load_dotenv

load_dotenv()

HF_SPACE_URL = os.getenv("HF_SPACE_URL", "AhmedAlmaghz/Kolors-Virtual-Try-On")
HF_TOKEN = os.getenv("HF_TOKEN", None)
MAX_CONCURRENT = int(os.getenv("MAX_CONCURRENT", "5"))
API_KEY = os.getenv("API_KEY", None)
