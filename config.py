import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("8470946919:AAG55k7H7TFUUqdEgi9LL269OD9bOFY32es")
AUDIO_API_KEY = os.getenv("hfg")
LASTFM_API_KEY = os.getenv("LASTFM_API_KEY", "")   # <-- اضافه شد
ADMINS = [int(x) for x in os.getenv("SUPERBOT_ADMINS", "").split(",") if x.strip()]
PROXY_HEALTH_INTERVAL = int(os.getenv("PROXY_HEALTH_INTERVAL", 60 * 15))
PROXY_MAX_TRIES = int(os.getenv("PROXY_MAX_TRIES", 6))
MAX_SIZE_MB = int(os.getenv("MAX_SIZE_MB", 1900))
DATA_DIR = Path(os.getenv("DATA_DIR", "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)



