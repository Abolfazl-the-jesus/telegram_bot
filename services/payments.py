import secrets
from typing import Optional
from services.database import create_order, mark_order_paid, get_order_by_ref


def generate_ref(prefix: str = "ord") -> str:
    return f"{prefix}_{secrets.token_urlsafe(8)}"


async def create_stars_order(user_id: int, credits: int, stars: int) -> str:
    ref = generate_ref("stars")
    await create_order(user_id=user_id, amount=credits, provider="stars", ref=ref)
    return ref

async def create_bank_order(user_id: int, credits: int) -> str:
    ref = generate_ref("bank")
    await create_order(user_id=user_id, amount=credits, provider="bank", ref=ref)
    return ref

async def create_ton_order(user_id: int, credits: int) -> str:
    ref = generate_ref("ton")
    await create_order(user_id=user_id, amount=credits, provider="ton", ref=ref)
    return ref


async def verify_and_apply_payment(ref: str) -> bool:
    # Placeholder: call provider API to verify; here we mark paid directly for demo
    ok = await mark_order_paid(ref)
    return ok


