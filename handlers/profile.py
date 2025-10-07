# handlers/profile.py (اصلاح‌شده)
from aiogram import Router, F
from aiogram.types import Message
# کیبورد در same package handlers/keyboard.py قرار دارد -> import صحیح:
from handlers.keyboard import gender_kb, provinces_kb, cities_kb
import services.database as db

router = Router()

@router.message(F.command == "start")
async def start_cmd(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or ""
    await db.create_user_if_not_exists(user_id, username)
    await db.set_username(user_id, username)
    if await db.is_profile_complete(user_id):
        await message.answer("👋 خوش اومدی! پروفایل شما کامل است. برای ورود به چت ناشناس /chat را بزن.")
    else:
        await message.answer("سلام! بیایم پروفایلت رو بسازیم.\nجنسیتت رو انتخاب کن:", reply_markup=gender_kb)

@router.message(F.text.in_({"👨 پسر", "👩 دختر"}))
async def set_gender_handler(message: Message):
    user_id = message.from_user.id
    gender = "male" if "پسر" in message.text else "female"
    await db.set_gender(user_id, gender)
    await message.answer("✅ جنسیت ثبت شد. حالا استان خودت را انتخاب کن:", reply_markup=provinces_kb)

@router.message()
async def handle_province_and_city(message: Message):
    user_id = message.from_user.id
    text = (message.text or "").strip()
    provinces = {"کرمان": ["کرمان", "رفسنجان", "جیرفت"], "تهران": ["تهران", "ری", "شمیرانات"]}
    if text in provinces.keys():
        await db.set_province(user_id, text)
        await message.answer("استان ثبت شد. حالا شهرت رو انتخاب کن:", reply_markup=cities_kb(text))
        return
    for prov, cities in provinces.items():
        if text in cities:
            await db.set_city(user_id, text)
            await message.answer("✅ شهر ثبت شد. حالا لطفاً یک عکس پروفایل بفرست.")
            return
    # اگر پیام از نوع عکس بود، یا متن غیرمرتبط، آن را نادیده می‌گیریم و منتظر عکس می‌مانیم

@router.message(F.photo)
async def save_profile_pic(message: Message):
    user_id = message.from_user.id
    photo_id = message.photo[-1].file_id
    await db.set_profile_pic(user_id, photo_id)
    if await db.is_profile_complete(user_id):
        await message.answer("🎉 پروفایل کامل شد! حالا می‌تونی با دستور /chat وارد چت ناشناس بشی.")
    else:
        await message.answer("✅ عکس ذخیره شد. اما پروفایلت هنوز کامل نیست.")
