import os
import hmac
import hashlib
from typing import Dict, Any, Optional
import stripe
from services.database import create_order, mark_order_paid, get_order_by_ref

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY


async def create_checkout_session(user_id: int, amount_credits: int, price_cents: int, success_url: str, cancel_url: str) -> Dict[str, Any]:
    if not STRIPE_SECRET_KEY:
        raise RuntimeError("Stripe not configured")
    ref = f"user{user_id}_{amount_credits}"
    order_id = await create_order(user_id, amount_credits, provider="stripe", ref=ref)
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'product_data': {'name': f'Credits x{amount_credits}'},
                'unit_amount': price_cents,
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url=success_url,
        cancel_url=cancel_url,
        client_reference_id=ref,
    )
    return {"id": session.id, "url": session.url, "order_id": order_id, "ref": ref}


async def handle_stripe_webhook(payload: bytes, sig_header: str) -> bool:
    if not STRIPE_WEBHOOK_SECRET:
        return False
    try:
        event = stripe.Webhook.construct_event(
            payload=payload, sig_header=sig_header, secret=STRIPE_WEBHOOK_SECRET
        )
    except Exception:
        return False

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        ref = session.get('client_reference_id')
        if ref:
            await mark_order_paid(ref)
            return True
    return False

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


