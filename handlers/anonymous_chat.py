# src/bot/handlers/anonymous_chat.py
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
import services.matcher as matcher
import services.database as db

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

    # (optional) parse filter from text or use defaults
    # for now we use no filter (None)
    partner = await matcher.enqueue_search(user_id)
    if partner:
        await message.reply("✅ فردی پیدا شد — چت شروع شد! برای پایان '❌ پایان چت' را بزن.")
    else:
        await message.reply("⌛ شما در صف جستجو قرار گرفتید؛ به محض پیدا شدن فردی اطلاع می‌دهیم.")
