import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Bot and APIs
TOKEN = os.getenv("BOT_TOKEN", "")
AUDIO_API_KEY = os.getenv("AUDIO_API_KEY", "")
LASTFM_API_KEY = os.getenv("LASTFM_API_KEY", "")

# Admins (comma-separated IDs)
ADMINS = [int(x) for x in os.getenv("SUPERBOT_ADMINS", "").split(",") if x.strip()]

# Proxy/Downloader config
PROXY_HEALTH_INTERVAL = int(os.getenv("PROXY_HEALTH_INTERVAL", 60 * 15))
PROXY_MAX_TRIES = int(os.getenv("PROXY_MAX_TRIES", 6))
MAX_SIZE_MB = int(os.getenv("MAX_SIZE_MB", 1900))

# Data dirs
DATA_DIR = Path(os.getenv("DATA_DIR", "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Credits
CREDIT_COST_RANDOM = int(os.getenv("CREDIT_COST_RANDOM", 1))
CREDIT_COST_ADVANCED = int(os.getenv("CREDIT_COST_ADVANCED", 2))



