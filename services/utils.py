import logging

logger = logging.getLogger('superbot')

def ensure_dir(path):
    path.mkdir(parents=True, exist_ok=True)