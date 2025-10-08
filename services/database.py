# src/services/database.py
import os
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy import (
    Column, Integer, BigInteger, String, Text, DateTime, ForeignKey, func, Boolean, Index, UniqueConstraint
)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import select, and_, or_, update
from sqlalchemy.exc import IntegrityError

DATABASE_URL = os.getenv("DATABASE_URL", "")
if not DATABASE_URL:
    DATABASE_URL = "sqlite+aiosqlite:///./data/bot_dev.db"

engine = create_async_engine(DATABASE_URL, echo=False, future=True)
AsyncSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()


# ---------------- Models ----------------
class User(Base):
    __tablename__ = "users"
    id = Column(BigInteger, primary_key=True, index=True)  # telegram user id
    username = Column(String(100), nullable=True, default="")
    gender = Column(String(16), nullable=True)
    province = Column(String(128), nullable=True)
    city = Column(String(128), nullable=True)
    profile_pic = Column(String(512), nullable=True)
    status = Column(String(32), nullable=False, default="idle")  # idle, searching, chatting
    partner_id = Column(BigInteger, nullable=True)
    credits = Column(Integer, nullable=False, default=10)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Invite(Base):
    __tablename__ = "invites"
    code = Column(String(64), primary_key=True)
    inviter_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class UsedInvite(Base):
    __tablename__ = "used_invites"
    user_id = Column(BigInteger, primary_key=True)
    code = Column(String(64), nullable=False)
    used_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        UniqueConstraint('code', name='uq_used_invites_code'),
    )


class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True, autoincrement=True)
    reporter_id = Column(BigInteger, nullable=False)
    reported_id = Column(BigInteger, nullable=False)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Block(Base):
    __tablename__ = "blocks"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    blocked_id = Column(BigInteger, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        UniqueConstraint('user_id', 'blocked_id', name='uq_blocks_pair'),
    )


class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_a = Column(BigInteger, nullable=False)
    user_b = Column(BigInteger, nullable=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(32), nullable=False, default="active")  # active, ended, cancelled


class UserPrefs(Base):
    __tablename__ = "user_prefs"
    user_id = Column(BigInteger, ForeignKey("users.id"), primary_key=True)
    best_quality = Column(String(32), nullable=True)


class UserCookie(Base):
    __tablename__ = "user_cookies"
    user_id = Column(BigInteger, ForeignKey("users.id"), primary_key=True)
    enc_path = Column(String(512), nullable=False)


class Proxy(Base):
    __tablename__ = "proxies"
    id = Column(Integer, primary_key=True, autoincrement=True)
    proxy = Column(String(256), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    active = Column(Boolean, nullable=False, default=True)
    failed_count = Column(Integer, nullable=False, default=0)
    quarantine = Column(Boolean, nullable=False, default=False)

Index('ix_users_status_created', User.status, User.created_at)


class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    amount = Column(Integer, nullable=False)  # credits to add
    provider = Column(String(32), nullable=False)  # e.g., zarinpal, zibal, manual
    ref = Column(String(128), unique=True, nullable=False)
    status = Column(String(16), nullable=False, default="pending")  # pending, paid, failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    paid_at = Column(DateTime(timezone=True), nullable=True)


# Likes / Favorites
class Like(Base):
    __tablename__ = "likes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    liked_user_id = Column(BigInteger, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        UniqueConstraint('user_id', 'liked_user_id', name='uq_likes_pair'),
        Index('ix_likes_liked_user_id', 'liked_user_id'),
    )


class FavoriteRequest(Base):
    __tablename__ = "favorite_requests"
    id = Column(Integer, primary_key=True, autoincrement=True)
    requester_id = Column(BigInteger, nullable=False)
    target_id = Column(BigInteger, nullable=False)
    status = Column(String(16), nullable=False, default='pending')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    __table_args__ = (
        UniqueConstraint('requester_id', 'target_id', name='uq_favreq_pair'),
    )


class Favorite(Base):
    __tablename__ = "favorites"
    id = Column(Integer, primary_key=True, autoincrement=True)
    owner_id = Column(BigInteger, nullable=False)
    favorite_user_id = Column(BigInteger, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        UniqueConstraint('owner_id', 'favorite_user_id', name='uq_favorites_pair'),
    )


# ---------------- Orders CRUD ----------------
async def create_order(user_id: int, amount: int, provider: str, ref: str) -> int:
    async with AsyncSessionLocal() as session:
        async with session.begin():
            o = Order(user_id=user_id, amount=amount, provider=provider, ref=ref, status="pending")
            session.add(o)
            await session.flush()
            return o.id

async def get_order_by_ref(ref: str) -> Optional[Dict[str, Any]]:
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(Order).where(Order.ref == ref))
        o = res.scalar_one_or_none()
        if not o:
            return None
        return {"id": o.id, "user_id": o.user_id, "amount": o.amount, "provider": o.provider, "ref": o.ref, "status": o.status}

async def mark_order_paid(ref: str) -> bool:
    async with AsyncSessionLocal() as session:
        async with session.begin():
            res = await session.execute(select(Order).where(Order.ref == ref))
            o = res.scalar_one_or_none()
            if not o or o.status == "paid":
                return False
            o.status = "paid"
            o.paid_at = func.now()
            u = await session.get(User, o.user_id)
            if u:
                u.credits += o.amount
            return True


# ---------------- Init ----------------
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# ---------------- Utility / CRUD ----------------
async def create_user_if_not_exists(user_id: int, username: Optional[str] = "") -> None:
    async with AsyncSessionLocal() as session:
        async with session.begin():
            u = await session.get(User, user_id)
            if u is None:
                user = User(id=user_id, username=username or "", credits=10)
                session.add(user)


async def set_username(user_id: int, username: str):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            u = await session.get(User, user_id)
            if u:
                u.username = username or u.username
            else:
                session.add(User(id=user_id, username=username or "", credits=10))
async def is_profile_complete(user_id: int) -> bool:
    async with AsyncSessionLocal() as session:
        res = await session.execute(
            select(User.gender, User.province, User.city, User.profile_pic).where(User.id == user_id)
        )
        row = res.first()
        return bool(row and all(row))


# profile setters
async def set_gender(user_id: int, gender: str):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            u = await session.get(User, user_id)
            if u:
                u.gender = gender

async def set_province(user_id: int, province: str):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            u = await session.get(User, user_id)
            if u:
                u.province = province

async def set_city(user_id: int, city: str):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            u = await session.get(User, user_id)
            if u:
                u.city = city

async def set_profile_pic(user_id: int, file_id: str):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            u = await session.get(User, user_id)
            if u:
                u.profile_pic = file_id


# credits
async def get_credits(user_id: int) -> int:
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(User.credits).where(User.id == user_id))
        r = res.scalar_one_or_none()
        return int(r) if r is not None else 0

async def add_credits(user_id: int, amount: int = 1):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            u = await session.get(User, user_id)
            if u:
                u.credits += amount
            else:
                session.add(User(id=user_id, credits=amount))


async def consume_credit(user_id: int, amount: int = 1) -> bool:
    """
    Atomically consume credits. Returns True if successful.
    """
    async with AsyncSessionLocal() as session:
        async with session.begin():
            stmt = select(User).where(User.id == user_id).with_for_update()
            res = await session.execute(stmt)
            user = res.scalar_one_or_none()
            if not user or user.credits < amount:
                return False
            user.credits -= amount
            return True


# invites
async def create_invite(code: str, inviter_id: int) -> bool:
    async with AsyncSessionLocal() as session:
        async with session.begin():
            try:
                inv = Invite(code=code, inviter_id=inviter_id)
                session.add(inv)
                return True
            except IntegrityError:
                return False

async def use_invite_for_user(code: str, new_user_id: int) -> bool:
    async with AsyncSessionLocal() as session:
        async with session.begin():
            inv = await session.get(Invite, code)
            if not inv:
                return False
            used = await session.get(UsedInvite, new_user_id)
            if used:
                return False
            # enforce single-use invite code
            existing_use = await session.execute(select(UsedInvite).where(UsedInvite.code == code))
            if existing_use.scalar_one_or_none():
                return False
            u = await session.get(User, new_user_id)
            if not u:
                session.add(User(id=new_user_id, credits=5))
            else:
                u.credits += 5
            inviter = await session.get(User, inv.inviter_id)
            if inviter:
                inviter.credits += 5
            else:
                session.add(User(id=inv.inviter_id, credits=5))
            ui = UsedInvite(user_id=new_user_id, code=code)
            session.add(ui)
            return True

async def get_invite_for_user(inviter_id: int) -> Optional[str]:
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(Invite.code).where(Invite.inviter_id == inviter_id))
        row = res.scalar_one_or_none()
        return row
# status / matching helpers & session management
async def set_status(user_id: int, status: str, partner_id: Optional[int] = None):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            u = await session.get(User, user_id)
            if u:
                u.status = status
                u.partner_id = partner_id

async def get_status(user_id: int) -> Tuple[str, Optional[int]]:
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(User.status, User.partner_id).where(User.id == user_id))
        row = res.first()
        if not row:
            return ("idle", None)
        return (row[0], row[1])


async def find_partner_candidate(user_id: int, gender: Optional[str] = None, province: Optional[str] = None, city: Optional[str] = None) -> Optional[int]:
    """
    Find one candidate row with FOR UPDATE SKIP LOCKED. This is used by matcher to lock candidate.
    """
    async with AsyncSessionLocal() as session:
        async with session.begin():
            stmt = select(User).where(User.status == 'searching', User.id != user_id)
            if gender:
                stmt = stmt.where(User.gender == gender)
            if province:
                stmt = stmt.where(User.province == province)
            if city:
                stmt = stmt.where(User.city == city)
            stmt = stmt.order_by(User.created_at).with_for_update(skip_locked=True).limit(1)
            res = await session.execute(stmt)
            cand = res.scalar_one_or_none()
            return cand.id if cand else None


async def get_online_users(limit: int = 50) -> List[Dict[str, Any]]:
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(User).where(User.status == 'idle').limit(limit))
        rows = res.scalars().all()
        return [{"user_id": r.id, "username": r.username, "gender": r.gender, "province": r.province, "city": r.city} for r in rows]


# blocks / reports
async def block_user(user_id: int, blocked_id: int):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            b = Block(user_id=user_id, blocked_id=blocked_id)
            session.add(b)

async def is_blocked(a: int, b: int) -> bool:
    async with AsyncSessionLocal() as session:
        res = await session.execute(
            select(Block).where(
                or_(
                    and_(Block.user_id == a, Block.blocked_id == b),
                    and_(Block.user_id == b, Block.blocked_id == a)
                )
            ).limit(1)
        )
        return res.scalar_one_or_none() is not None

async def report_user(reporter_id: int, reported_id: int, reason: str = ""):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            r = Report(reporter_id=reporter_id, reported_id=reported_id, reason=reason)
            session.add(r)

async def list_reports(limit: int = 100):
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(Report).order_by(Report.created_at.desc()).limit(limit))
        return [dict(id=r.id, reporter_id=r.reporter_id, reported_id=r.reported_id, reason=r.reason, created_at=r.created_at) for r in res.scalars().all()]


# chat sessions
async def create_chat_session(user_a: int, user_b: int) -> int:
    async with AsyncSessionLocal() as session:
        async with session.begin():
            cs = ChatSession(user_a=user_a, user_b=user_b)
            session.add(cs)
            await session.flush()
            return cs.id

async def end_chat_session(session_id: int):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            cs = await session.get(ChatSession, session_id)
            if cs and cs.status == "active":
                cs.status = "ended"
                cs.ended_at = func.now()


# ---------------- User Prefs / Cookies ----------------
async def get_user_best_quality(user_id: int) -> Optional[str]:
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(UserPrefs.best_quality).where(UserPrefs.user_id == user_id))
        return res.scalar_one_or_none()

async def set_user_best_quality(user_id: int, best_quality: str) -> None:
    async with AsyncSessionLocal() as session:
        async with session.begin():
            row = await session.get(UserPrefs, user_id)
            if row is None:
                session.add(UserPrefs(user_id=user_id, best_quality=best_quality))
            else:
                row.best_quality = best_quality

async def set_user_cookie_path(user_id: int, enc_path: str) -> None:
    async with AsyncSessionLocal() as session:
        async with session.begin():
            row = await session.get(UserCookie, user_id)
            if row is None:
                session.add(UserCookie(user_id=user_id, enc_path=enc_path))
            else:
                row.enc_path = enc_path

async def get_user_cookie_path(user_id: int) -> Optional[str]:
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(UserCookie.enc_path).where(UserCookie.user_id == user_id))
        return res.scalar_one_or_none()


# ---------------- Proxies CRUD ----------------
async def add_proxy_to_db(proxy: str) -> bool:
    async with AsyncSessionLocal() as session:
        async with session.begin():
            exists = await session.execute(select(Proxy).where(Proxy.proxy == proxy))
            if exists.scalar_one_or_none():
                return False
            session.add(Proxy(proxy=proxy, active=True, quarantine=False, failed_count=0))
            return True

async def remove_proxy_from_db(proxy: str) -> None:
    async with AsyncSessionLocal() as session:
        async with session.begin():
            res = await session.execute(select(Proxy).where(Proxy.proxy == proxy))
            row = res.scalar_one_or_none()
            if row:
                await session.delete(row)

async def list_proxies_from_db(limit: int = 100):
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(Proxy.id, Proxy.proxy, Proxy.created_at, Proxy.updated_at, Proxy.active, Proxy.failed_count).limit(limit))
        return res.all()

async def get_active_proxies_from_db(limit: int = 50):
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(Proxy.proxy).where(Proxy.active == True, Proxy.quarantine == False).limit(limit))
        return [r for r in res.scalars().all()]

async def mark_proxy_failed_in_db(proxy: str) -> None:
    async with AsyncSessionLocal() as session:
        async with session.begin():
            res = await session.execute(select(Proxy).where(Proxy.proxy == proxy))
            row = res.scalar_one_or_none()
            if row:
                row.failed_count += 1
                if row.failed_count >= 3:
                    row.active = False

async def mark_proxy_ok_in_db(proxy: str) -> None:
    async with AsyncSessionLocal() as session:
        async with session.begin():
            res = await session.execute(select(Proxy).where(Proxy.proxy == proxy))
            row = res.scalar_one_or_none()
            if row:
                row.failed_count = 0
                row.active = True
                row.quarantine = False

async def quarantine_proxy_in_db(proxy: str) -> None:
    async with AsyncSessionLocal() as session:
        async with session.begin():
            res = await session.execute(select(Proxy).where(Proxy.proxy == proxy))
            row = res.scalar_one_or_none()
            if row:
                row.quarantine = True
                row.active = False
            else:
                session.add(Proxy(proxy=proxy, active=False, quarantine=True, failed_count=0))
async def get_session_by_user(user_id: int) -> Optional[Dict[str, Any]]:
    async with AsyncSessionLocal() as session:
        res = await session.execute(
            select(ChatSession).where(
                and_(
                    ChatSession.status == "active",
                    or_(ChatSession.user_a == user_id, ChatSession.user_b == user_id)
                )
            ).limit(1)
        )
        cs = res.scalar_one_or_none()
        if not cs:
            return None
        return {"id": cs.id, "user_a": cs.user_a, "user_b": cs.user_b, "started_at": cs.started_at, "last_activity": cs.last_activity}

async def end_chat_session_by_users(user_a: int, user_b: int):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            res = await session.execute(select(ChatSession).where(
                and_(
                    ChatSession.status == "active",
                    or_(
                        and_(ChatSession.user_a == user_a, ChatSession.user_b == user_b),
                        and_(ChatSession.user_a == user_b, ChatSession.user_b == user_a)
                    )
                )
            ).limit(1))
            cs = res.scalar_one_or_none()
            if cs:
                cs.status = "ended"
                cs.ended_at = func.now()

async def update_session_activity(session_id: int):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            cs = await session.get(ChatSession, session_id)
            if cs:
                cs.last_activity = func.now()

async def end_expired_sessions(max_seconds: int = 3600) -> int:
    """
    End sessions with last_activity older than max_seconds.
    Returns number of sessions ended.
    """
    import datetime
    # NOTE: sqlite syntax for datetime funcs differs; use python fallback for sqlite.
    if DATABASE_URL.startswith("sqlite"):
        # fallback implementation: select and compare in python
        async with AsyncSessionLocal() as session:
            async with session.begin():
                res = await session.execute(select(ChatSession).where(ChatSession.status == "active"))
                ended = 0
                from datetime import datetime, timezone, timedelta
                for cs in res.scalars().all():
                    if cs.last_activity:
                        # cs.last_activity is datetime
                        if (datetime.now(timezone.utc) - cs.last_activity) .total_seconds() > max_seconds:
                            cs.status = "ended"
                            cs.ended_at = func.now()
                            ended += 1
                return ended
    else:
        # For Postgres, do atomic update
        async with AsyncSessionLocal() as session:
            async with session.begin():
                # use raw update with interval
                await session.execute(
                    update(ChatSession).
                    where(ChatSession.status == "active").
                    where(ChatSession.last_activity < func.now() - func.cast(f'{max_seconds} seconds', Text))
                )
                # For simplicity return 0 here (counting would require RETURNING which SQLAlchemy async may support).
                return 0               