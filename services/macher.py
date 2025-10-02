# src/services/matcher.py
import asyncio
from typing import Optional

from sqlalchemy import select, and_
from sqlalchemy.exc import SQLAlchemyError

from services.database import AsyncSessionLocal, User

# Timeout برای تلاش اولیه (ثانیه)
MATCH_ATTEMPT_TIMEOUT = 5


async def enqueue_search(user_id: int, gender: Optional[str] = None, province: Optional[str] = None) -> Optional[int]:
    """
    Try to enqueue user for matching and immediately attempt to find a partner.
    Returns partner_id if matched, otherwise None (user remains in searching state).
    This function performs an atomic DB transaction for matching + consuming credits.
    """
    async with AsyncSessionLocal() as session:
        async with session.begin():
            # Ensure user exists
            me = await session.get(User, user_id)
            if me is None:
                # create a new user record with default credits (10)
                me = User(id=user_id, credits=10)
                session.add(me)
                await session.flush()  # ensure me.id exists

            # basic checks
            if me.credits < 1:
                # insufficient credits -> do not set searching
                return None

            # set me to searching (so candidate query won't match me)
            me.status = "searching"
            me.partner_id = None

            # build candidate query
            stmt = select(User).where(
                User.status == "searching",
                User.id != user_id
            )
            if gender:
                stmt = stmt.where(User.gender == gender)
            if province:
                stmt = stmt.where(User.province == province)

            # Lock candidate row (skip locked) to avoid races
            stmt = stmt.order_by(User.created_at).with_for_update(skip_locked=True).limit(1)
            res = await session.execute(stmt)
            candidate = res.scalar_one_or_none()

            if not candidate:
                # no candidate right now; keep user searching in DB
                return None

            # Now we have a candidate row locked in this transaction.
            # Re-fetch current me row FOR UPDATE to ensure consistent credits check
            me_locked_stmt = select(User).where(User.id == user_id).with_for_update()
            me_res = await session.execute(me_locked_stmt)
            me_locked = me_res.scalar_one()

            # Check credits again
            if (me_locked.credits or 0) < 1 or (candidate.credits or 0) < 1:
                # one of them lacks credits; rollback matching attempt
                # set candidate back to idle, leave me in searching or set idle
                candidate.status = "idle"
                candidate.partner_id = None
                me_locked.status = "idle"
                me_locked.partner_id = None
                return None

            # consume credits atomically
            me_locked.credits -= 1
            candidate.credits -= 1

            # set chatting state and partner ids
            me_locked.status = "chatting"
            me_locked.partner_id = candidate.id
            candidate.status = "chatting"
            candidate.partner_id = me_locked.id

            # commit happens at context exit
            return candidate.id


async def cancel_search(user_id: int):
    """
    Cancel a searching request (set to idle).
    """
    async with AsyncSessionLocal() as session:
        async with session.begin():
            u = await session.get(User, user_id)
            if u:
                if u.status == "searching":
                    u.status = "idle"
                    u.partner_id = None


async def get_searching_count() -> int:
    async with AsyncSessionLocal() as session:
        async with session.begin():
            res = await session.execute(select(User.id).where(User.status == "searching"))
            rows = res.scalars().all()
            return len(rows)
