# src/services/workers/session_manager.py
import asyncio
import logging
from services.database import end_expired_sessions

logger = logging.getLogger("session_manager")
logger.setLevel(logging.INFO)

async def session_cleaner_loop(interval_seconds: int = 60, max_idle_seconds: int = 3600):
    """
    Every interval_seconds run end_expired_sessions(max_idle_seconds).
    """
    while True:
        try:
            ended = await end_expired_sessions(max_seconds=max_idle_seconds)
            if ended:
                logger.info("Ended %d expired sessions", ended)
        except Exception as e:
            logger.exception("session_cleaner error: %s", e)
        await asyncio.sleep(interval_seconds)