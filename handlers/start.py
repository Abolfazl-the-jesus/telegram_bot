from aiogram import Router, types
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from config import ADMINS

router = Router()

MAIN_BUTTONS = [
    [KeyboardButton(text="download"), KeyboardButton(text="findsong")]
]

ADMIN_BUTTON_ROW = [KeyboardButton(text="addproxy")]

@router.message(CommandStart())
async def start_cmd(message: types.Message):
    # ساخت دکمه‌ها
    buttons = MAIN_BUTTONS.copy()
    # اگر ادمین بود دکمه پنل ادمین هم اضافه کن
    if message.from_user.id in ADMINS:
        buttons.append(ADMIN_BUTTON_ROW)
    keyboard = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
    await message.answer(
        "سلام 👋\nبه ربات خوش آمدید!\nاز دکمه‌های زیر برای استفاده از بخش‌های مختلف استفاده کنید.",
        reply_markup=keyboard
    )