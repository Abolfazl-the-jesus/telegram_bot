# src/services/matcher.py
from typing import Optional, Tuple
from services.database import AsyncSessionLocal, User, create_chat_session
from sqlalchemy import select

async def enqueue_search(user_id: int, gender: Optional[str] = None, province: Optional[str] = None, city: Optional[str] = None) -> Optional[Tuple[int,int]]:
    """
    Try atomic match: returns tuple (partner_id, session_id) if matched, else None.
    """
    async with AsyncSessionLocal() as session:
        async with session.begin():
            me = await session.get(User, user_id)
            if me is None:
                me = User(id=user_id, credits=10)
                session.add(me)
                await session.flush()

            if (me.credits or 0) < 1:
                return None

            me.status = "searching"
            me.partner_id = None

            # candidate query
            stmt = select(User).where(User.status == 'searching', User.id != user_id)
            if gender:
                stmt = stmt.where(User.gender == gender)
            if province:
                stmt = stmt.where(User.province == province)
            if city:
                stmt = stmt.where(User.city == city)
            stmt = stmt.order_by(User.created_at).with_for_update(skip_locked=True).limit(1)
            res = await session.execute(stmt)
            candidate = res.scalar_one_or_none()
            if not candidate:
                return None

            # lock me row
            me_stmt = select(User).where(User.id == user_id).with_for_update()
            res2 = await session.execute(me_stmt)
            me_locked = res2.scalar_one()

            if me_locked.credits < 1 or candidate.credits < 1:
                candidate.status = 'idle'
                candidate.partner_id = None
                me_locked.status = 'idle'
                me_locked.partner_id = None
                return None

            me_locked.credits -= 1
            candidate.credits -= 1

            me_locked.status = 'chatting'
            me_locked.partner_id = candidate.id
            candidate.status = 'chatting'
            candidate.partner_id = me_locked.id

            # create chat session
            cs_id = await create_chat_session(me_locked.id, candidate.id)
            return (candidate.id, cs_id)



