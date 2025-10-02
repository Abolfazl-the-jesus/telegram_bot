# services/database.py
import os
from typing import Optional, List, Dict, Any

from sqlalchemy import (
    Column, Integer, BigInteger, String, Text, DateTime, ForeignKey, func, Boolean, Index
)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy import select, update, insert, and_, or_, literal_column
from sqlalchemy.exc import IntegrityError

DATABASE_URL = os.getenv("DATABASE_URL", "")  # e.g. postgresql+asyncpg://user:pass@host/db
USE_SQLITE_FALLBACK = False
if not DATABASE_URL:
    # fallback to local sqlite async for dev
    DATABASE_URL = "sqlite+aiosqlite:///./data/bot_dev.db"
    USE_SQLITE_FALLBACK = True

# create engine & session
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

    # relationships not strictly necessary here

Index("ix_users_status", User.status)


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

Index("ix_blocks_pair", Block.user_id, Block.blocked_id)


# ---------------- Utility / Init ----------------
async def init_db():
    """
    Create tables if not exist. For production, use Alembic migrations instead.
    Call this at bot startup for dev convenience, or run alembic for prod.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# ---------------- CRUD / Business Logic (async) ----------------

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
        result = await session.execute(
            select(User.gender, User.province, User.city, User.profile_pic).where(User.id == user_id)
        )
        row = result.first()
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
        result = await session.execute(select(User.credits).where(User.id == user_id))
        r = result.scalar_one_or_none()
        return int(r) if r is not None else 0

async def add_credits(user_id: int, amount: int = 1):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            u = await session.get(User, user_id)
            if u:
                u.credits = u.credits + amount
            else:
                session.add(User(id=user_id, credits=amount))

async def consume_credit(user_id: int, amount: int = 1) -> bool:
    """
    Atomically consume credits using SELECT ... FOR UPDATE to avoid race conditions.
    Returns True if successful, False if insufficient credits.
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
    """
    Apply invite: if exists and not used by this user -> give +5 to inviter and new_user (record usage).
    """
    async with AsyncSessionLocal() as session:
        async with session.begin():
            # ensure invite exists
            inv = await session.get(Invite, code)
            if not inv:
                return False
            # check if new_user already used invite
            used = await session.execute(select(UsedInvite).where(UsedInvite.user_id == new_user_id))
            if used.scalar_one_or_none():
                return False
            # ensure user record exists
            u = await session.get(User, new_user_id)
            if not u:
                session.add(User(id=new_user_id, credits=5))
            else:
                u.credits += 5
            # give inviter +5
            inviter = await session.get(User, inv.inviter_id)
            if inviter:
                inviter.credits += 5
            else:
                session.add(User(id=inv.inviter_id, credits=5))
            # record usage
            ui = UsedInvite(user_id=new_user_id, code=code)
            session.add(ui)
            return True


# status / matching (basic, DB-backed)
async def set_status(user_id: int, status: str, partner_id: Optional[int] = None):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            u = await session.get(User, user_id)
            if u:
                u.status = status
                u.partner_id = partner_id

async def get_status(user_id: int) -> (str, Optional[int]):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User.status, User.partner_id).where(User.id == user_id))
        row = result.first()
        if not row:
            return ("idle", None)
        return (row[0], row[1])


async def find_partner(user_id: int, gender: Optional[str] = None, province: Optional[str] = None) -> Optional[int]:
    """
    Find a candidate who is searching. Use transaction + SELECT ... FOR UPDATE to avoid double-matching.
    Note: for large scale, use Redis queue instead of DB scans.
    """
    async with AsyncSessionLocal() as session:
        async with session.begin():
            # choose candidate
            stmt = select(User).where(
                User.status == 'searching',
                User.id != user_id
            )
            if gender:
                stmt = stmt.where(User.gender == gender)
            if province:
                stmt = stmt.where(User.province == province)
            stmt = stmt.order_by(User.created_at).with_for_update(skip_locked=True).limit(1)
            res = await session.execute(stmt)
            candidate = res.scalar_one_or_none()
            if not candidate:
                return None
            # set both to chatting and partner id
            me = await session.get(User, user_id)
            if not me:
                return None
            me.status = "chatting"
            me.partner_id = candidate.id
            candidate.status = "chatting"
            candidate.partner_id = user_id
            return candidate.id


async def get_online_users(limit: int = 50) -> List[Dict[str, Any]]:
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(User).where(User.status == 'idle').limit(limit))
        rows = res.scalars().all()
        return [
            {"user_id": r.id, "username": r.username, "gender": r.gender, "province": r.province, "city": r.city}
            for r in rows
        ]


# blocks / reports
async def block_user(user_id: int, blocked_id: int):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            b = Block(user_id=user_id, blocked_id=blocked_id)
            session.add(b)

async def is_blocked(a: int, b: int) -> bool:
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(Block).where(
            or_(
                and_(Block.user_id == a, Block.blocked_id == b),
                and_(Block.user_id == b, Block.blocked_id == a)
            )
        ).limit(1))
        return res.scalar_one_or_none() is not None

async def report_user(reporter_id: int, reported_id: int, reason: str = ""):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            r = Report(reporter_id=reporter_id, reported_id=reported_id, reason=reason)
            session.add(r)
