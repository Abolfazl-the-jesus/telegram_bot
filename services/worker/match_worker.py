# src/services/workers/match_worker.py
import asyncio
import logging
from typing import Optional

from services.matcher import enqueue_search
from services.database import AsyncSessionLocal, User, select

logger = logging.getLogger("match_worker")
logger.setLevel(logging.INFO)


async def scan_and_match_loop(interval_seconds: int = 2):
    """
    Background loop: scan for users in 'searching' and try to match them pairwise.
    This is a fallback worker — ideally matching is immediate in enqueue_search,
    but this ensures eventual pairing.
    """
    while True:
        try:
            # fetch a list of searching users (small batch)
            async with AsyncSessionLocal() as session:
                async with session.begin():
                    res = await session.execute(select(User.id).where(User.status == "searching").limit(50))
                    ids = [r for r in res.scalars().all()]

            # try to match each id (best-effort)
            for uid in ids:
                # call matcher; it will try to find a candidate and match atomically
                partner = await enqueue_search(uid)
                if partner:
                    logger.info(f"Worker matched {uid} <-> {partner}")
                await asyncio.sleep(0)  # yield control

        except Exception as e:
            logger.exception("Error in match_worker loop: %s", e)

        await asyncio.sleep(interval_seconds)
