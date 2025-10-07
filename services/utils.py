import logging

logger = logging.getLogger('superbot')

def ensure_dir(path):
    path.mkdir(parents=True, exist_ok=True)

def sanitize_text(s: str, max_len: int = 2000) -> str:
    if not s:
        return ""
    s = s.replace("\x00", "?")
    if len(s) > max_len:
        s = s[:max_len]
    return s