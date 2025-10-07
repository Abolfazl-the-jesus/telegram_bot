# handlers/invite.py
from aiogram import Router, F
from aiogram.types import Message
import services.database as db
import secrets

router = Router()

@router.message(F.text == "/myinvite")
async def my_invite(message: Message):
    user_id = message.from_user.id
    await db.create_user_if_not_exists(user_id, message.from_user.username or "")
    # generate a simple code (if not exists, ensure unique)
    code = secrets.token_urlsafe(6)
    # try to insert; if collision (rare) regenerate
    ok = await db.create_invite(code, user_id)
    tries = 0
    while not ok and tries < 5:
        code = secrets.token_urlsafe(6)
        ok = await db.create_invite(code, user_id)
        tries += 1
    if not ok:
        return await message.answer("❌ خطا در تولید کد دعوت. دوباره تلاش کن.")
    await message.answer(f"کد دعوت شما: `{code}`\nوقتی کسی با این کد ثبت‌نام کند هر دو ۵ کردیت دریافت می‌کنید.", parse_mode="Markdown")

@router.message(F.text.startswith("/useinvite"))
async def use_invite(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return await message.answer("Usage: /useinvite <code>")
    code = parts[1].strip()
    user_id = message.from_user.id
    await db.create_user_if_not_exists(user_id, message.from_user.username or "")
    ok = await db.use_invite_for_user(code, user_id)
    if ok:
        await message.answer("✅ کد دعوت با موفقیت اعمال شد. ۵ کردیت به حساب شما افزوده شد.")
    else:
        await message.answer("❌ کد نامعتبر یا قبلاً استفاده شده است.")
