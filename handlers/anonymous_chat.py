# handlers/anonymous_chat.py (اصلاح‌شده)
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import services.database as db
# کیبوردها داخل پکیج handlers هستند -> از مسیر کامل وارد می‌کنیم
from handlers.keyboard import start_chat_kb, chat_actions_kb, invite_request_buttons

router = Router()

@router.message(F.text == "/chat")
async def enter_chat(message: Message):
    user_id = message.from_user.id
    db.create_user_if_not_exists(user_id, message.from_user.username or "")
    if not db.is_profile_complete(user_id):
        await message.answer("⚠️ قبل از چت ناشناس، لطفا پروفایل خود را کامل کنید. /start")
        return
    await message.answer("👤 می‌تونی جستجوی رندوم یا با فیلتر رو انتخاب کنی:", reply_markup=start_chat_kb)


@router.message(F.text == "🔎 جستجوی رندوم")
async def random_search(message: Message):
    user_id = message.from_user.id
    # بررسی کردیت
    if db.get_credits(user_id) < 1:
        await message.answer("❌ کردیت کافی نداری. از /myinvite یا خرید استفاده کن.")
        return
    db.set_status(user_id, "searching", None)
    partner = db.find_partner(user_id)
    if partner:
        # بررسی کردیت طرف مقابل
        if db.get_credits(partner) < 1:
            db.set_status(partner, "idle", None)
            await message.answer("⏳ طرف مقابل کردیت کافی نداشت؛ به دنبال فرد دیگری می‌گردم...")
            return
        # کاهش کردیت‌ها
        ok_u = db.consume_credit(user_id)
        ok_p = db.consume_credit(partner)
        if not ok_u or not ok_p:
            # اگر یکی ناموفق بود، بازگرد و پیام بده
            if ok_u:
                db.add_credits(user_id, 1)
            if ok_p:
                db.add_credits(partner, 1)
            await message.answer("❌ خطا در کم کردن کردیت‌ها؛ جستجو ادامه پیدا می‌کند.")
            db.set_status(user_id, "searching", None)
            return
        # ست کردن چت
        db.set_status(user_id, "chatting", partner)
        db.set_status(partner, "chatting", user_id)
        await message.answer("✅ وصل شدی! می‌تونی پیام بفرستی. برای پایان چت از '❌ پایان چت' استفاده کن.", reply_markup=chat_actions_kb)
        try:
            await message.bot.send_message(partner, "✅ شما وصل شدید! طرف مقابل یک ناشناس است. برای پایان چت '❌ پایان چت' را بزن.", reply_markup=chat_actions_kb)
        except Exception:
            db.set_status(user_id, "idle", None)
            db.set_status(partner, "idle", None)
            await message.answer("⚠️ نتونستم طرف مقابل رو پیام بدم، جفت شدن لغو شد.")
    else:
        await message.answer("⌛ در صف جستجو قرار گرفتی؛ به محض پیدا شدن فردی اطلاع می‌دهیم.")


@router.message(F.text == "📋 لیست آنلاین")
async def list_online(message: Message):
    user_id = message.from_user.id
    users = db.get_online_users(limit=30)
    if not users:
        await message.answer("هیچ کاربری در حال حاضر آنلاین نیست.")
        return
    for u in users:
        if u["user_id"] == user_id:
            continue
        text = f"👤 کاربر: @{u['username'] or 'ناشناس'}\nجنسیت: {u['gender'] or '-'}\nاستان: {u['province'] or '-'}\nشهر: {u['city'] or '-'}"
        kb = invite_request_buttons(u['user_id'])
        await message.answer(text, reply_markup=kb)


@router.callback_query()
async def handle_invite_callbacks(callback):
    data = callback.data or ""
    user_id = callback.from_user.id
    if data.startswith("accept_req_"):
        requester = int(data.split("_")[-1])
        # چک‌ها
        if not db.is_profile_complete(user_id) or not db.is_profile_complete(requester):
            await callback.message.answer("هر دو طرف باید پروفایل کامل داشته باشند.")
            return await callback.answer()
        if db.get_credits(user_id) < 1 or db.get_credits(requester) < 1:
            await callback.message.answer("یکی از طرفین کردیت کافی ندارد.")
            return await callback.answer()
        if not db.consume_credit(user_id) or not db.consume_credit(requester):
            await callback.message.answer("خطا در کم کردن کردیت‌ها.")
            return await callback.answer()
        db.set_status(user_id, "chatting", requester)
        db.set_status(requester, "chatting", user_id)
        await callback.message.answer("✅ چت شروع شد. پیام‌هایتان را ارسال کنید.", reply_markup=chat_actions_kb)
        try:
            await callback.bot.send_message(requester, "✅ درخواست شما قبول شد. حالا می‌توانید چت کنید.", reply_markup=chat_actions_kb)
        except Exception:
            db.set_status(user_id, "idle", None)
            db.set_status(requester, "idle", None)
            await callback.message.answer("⚠️ خطا در اطلاع‌رسانی به درخواست‌کننده.")
        return await callback.answer()
    elif data.startswith("decline_req_"):
        requester = int(data.split("_")[-1])
        await callback.message.answer("❌ درخواست رد شد.")
        try:
            await callback.bot.send_message(requester, "❌ درخواست چت شما رد شد.")
        except Exception:
            pass
        return await callback.answer()


@router.message(F.text == "❌ پایان چت")
async def end_chat(message: Message):
    user_id = message.from_user.id
    status, partner = db.get_status(user_id)
    if status != "chatting" or not partner:
        await message.answer("⚠️ شما الان در حال چت نیستید.")
        return
    db.set_status(user_id, "idle", None)
    db.set_status(partner, "idle", None)
    await message.answer("🚪 چت تمام شد.", reply_markup=start_chat_kb)
    try:
        await message.bot.send_message(partner, "🚪 طرف مقابل چت را پایان داد.", reply_markup=start_chat_kb)
    except Exception:
        pass


@router.message()
async def relay_message(message: Message):
    user_id = message.from_user.id
    status, partner = db.get_status(user_id)
    if status == "chatting" and partner:
        if db.is_blocked(user_id, partner):
            await message.answer("⚠️ شما یا طرف مقابل بلاک کرده است.")
            return
        try:
            await message.bot.send_message(partner, message.text)
        except Exception:
            await message.answer("⚠️ خطا در ارسال پیام به طرف مقابل.")
