# src/bot/handlers/anonymous_chat.py
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
import services.matcher as matcher
import services.database as db
from config import CREDIT_COST_RANDOM, CREDIT_COST_ADVANCED
from handlers.keyboard import chat_actions_kb, buy_credit_kb
from aiogram import F
from services.database import get_online_users
from services.database import get_credits
from aiogram.types import ContentType
from aiogram.types import CallbackQuery
from services.payments import create_stars_order, create_bank_order, create_ton_order
import time

# simple in-memory rate limit: user_id -> last_ts
_last_msg_ts = {}

router = Router()

@router.message(Command("chat"))
async def cmd_chat(message: Message):
    user_id = message.from_user.id
    # ensure user exists
    await db.create_user_if_not_exists(user_id, message.from_user.username or "")
    # check profile completeness
    if not await db.is_profile_complete(user_id):
        await message.reply("⚠️ لطفاً ابتدا پروفایلت رو با /start کامل کن.")
        return
    # check credits
    credits = await db.get_credits(user_id)
    if credits < 1:
        await message.reply("❌ کردیت کافی نداری. با /myinvite یا خرید می‌تونی کردیت دریافت کنی.")
        return

    # default: random search without filters
    partner = await matcher.enqueue_search(user_id)
    if partner:
        await message.reply("✅ فردی پیدا شد — چت شروع شد!", reply_markup=chat_actions_kb)
    else:
        await message.reply("⌛ شما در صف جستجو قرار گرفتید؛ به محض پیدا شدن فردی اطلاع می‌دهیم.")


@router.message(Command("random"))
async def cmd_random(message: Message):
    user_id = message.from_user.id
    await db.create_user_if_not_exists(user_id, message.from_user.username or "")
    credits = await db.get_credits(user_id)
    if credits < CREDIT_COST_RANDOM:
        return await message.reply("❌ کردیت کافی نداری. یکی از بسته‌های زیر را انتخاب کن:", reply_markup=buy_credit_kb())
    partner = await matcher.enqueue_search(user_id)
    if partner:
        await message.reply("✅ اتصال رندوم برقرار شد!", reply_markup=chat_actions_kb)
    else:
        await message.reply("⌛ در صف جستجوی رندوم قرار گرفتی.")


@router.message(Command("advanced"))
async def cmd_advanced(message: Message):
    user_id = message.from_user.id
    await db.create_user_if_not_exists(user_id, message.from_user.username or "")
    # very simple parse: e.g. /advanced gender=female province=تهران
    text = message.text or ""
    gender = None
    province = None
    for token in text.split()[1:]:
        if token.startswith("gender="):
            gender = token.split("=",1)[1]
        if token.startswith("province="):
            province = token.split("=",1)[1]
    credits = await db.get_credits(user_id)
    if credits < CREDIT_COST_ADVANCED:
        return await message.reply("❌ برای جستجوی پیشرفته کردیت کافی نیست. یکی از بسته‌های زیر را انتخاب کن:", reply_markup=buy_credit_kb())
    partner = await matcher.enqueue_search(user_id, gender=gender, province=province)
    if partner:
        await message.reply("✅ اتصال پیشرفته برقرار شد!", reply_markup=chat_actions_kb)
    else:
        await message.reply("⌛ در صف جستجوی پیشرفته قرار گرفتی.")


@router.message(F.text.in_({"❌ پایان چت", "🚩 گزارش", "⛔ بلاک"}))
async def chat_actions(message: Message):
    user_id = message.from_user.id
    text = message.text
    status, partner_id = await db.get_status(user_id)
    if not partner_id:
        return await message.reply("در حال حاضر در چت فعالی نیستی.")
    if text == "❌ پایان چت":
        await db.set_status(user_id, "idle", None)
        await db.set_status(partner_id, "idle", None)
        await message.reply("چت پایان یافت.")
    elif text == "🚩 گزارش":
        await db.report_user(user_id, partner_id, reason="reported")
        await message.reply("گزارش ثبت شد.")
    elif text == "⛔ بلاک":
        await db.block_user(user_id, partner_id)
        await db.set_status(user_id, "idle", None)
        await db.set_status(partner_id, "idle", None)
        await message.reply("کاربر بلاک شد و چت پایان یافت.")


@router.message(F.content_type.in_({ContentType.TEXT, ContentType.STICKER, ContentType.PHOTO, ContentType.VOICE, ContentType.VIDEO}))
async def relay(message: Message):
    user_id = message.from_user.id
    status, partner_id = await db.get_status(user_id)
    if status != "chatting" or not partner_id:
        return
    # Simple rate limit: drop if user sends too fast (store nothing persistent here; extend later)
    now = time.monotonic()
    last = _last_msg_ts.get(user_id, 0)
    if now - last < 0.5:
        return
    _last_msg_ts[user_id] = now
    # basic relay: forward text or notify unsupported types
    if message.text:
        await message.bot.send_message(partner_id, message.text)
    elif message.sticker:
        await message.bot.send_sticker(partner_id, message.sticker.file_id)
    elif message.photo:
        await message.bot.send_photo(partner_id, message.photo[-1].file_id, caption=message.caption or "")
    elif message.voice:
        await message.bot.send_voice(partner_id, message.voice.file_id, caption=message.caption or "")
    elif message.video:
        await message.bot.send_video(partner_id, message.video.file_id, caption=message.caption or "")


@router.message(Command("online"))
async def list_online(message: Message):
    rows = await get_online_users(limit=20)
    if not rows:
        return await message.reply("کاربری آنلاین نیست.")
    lines = []
    for r in rows:
        lines.append(f"{r['username'] or r['user_id']} | {r['gender'] or '-'} | {r['province'] or '-'}")
    await message.reply("\n".join(lines))


@router.message(Command("balance"))
async def balance(message: Message):
    user_id = message.from_user.id
    await db.create_user_if_not_exists(user_id, message.from_user.username or "")
    c = await get_credits(user_id)
    await message.reply(f"موجودی کردیت: {c}")

@router.message(Command("buycredit"))
async def buycredit(message: Message):
    await message.reply("خرید کردیت:", reply_markup=buy_credit_kb())


@router.callback_query()
async def handle_buy_callbacks(callback: CallbackQuery):
    data = callback.data or ""
    await callback.answer()
    if data.startswith("buy_stars_"):
        # format: buy_stars_{credits}_{stars}
        _, _, credits, stars = data.split("_", 3)
        ref = await create_stars_order(callback.from_user.id, int(credits), int(stars))
        await callback.message.answer(f"سفارش ایجاد شد. کد پیگیری: {ref}\nبرای پرداخت {stars} Stars اقدام کنید. پس از تایید، کردیت به‌صورت خودکار اضافه می‌شود.")
    elif data == "buy_bank":
        ref = await create_bank_order(callback.from_user.id, 100)  # به‌صورت نمونه 100 کریت
        await callback.message.answer(f"سفارش بانکی ایجاد شد. کد پیگیری: {ref}\nلینک پرداخت به‌زودی فعال می‌شود.")
    elif data == "buy_ton":
        ref = await create_ton_order(callback.from_user.id, 100)
        await callback.message.answer(f"سفارش TON ایجاد شد. کد پیگیری: {ref}\nآدرس پرداخت TON به‌زودی اعلام می‌شود.")
