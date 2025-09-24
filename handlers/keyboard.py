# keyboards.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

gender_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="👨 پسر"), KeyboardButton(text="👩 دختر")]],
    resize_keyboard=True
)

provinces_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="کرمان"), KeyboardButton(text="تهران")]],
    resize_keyboard=True
)

def cities_kb(province: str):
    provinces = {
        "کرمان": ["کرمان", "رفسنجان", "جیرفت"],
        "تهران": ["تهران", "ری", "شمیرانات"]
    }
    cities = provinces.get(province, [])
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=c)] for c in cities], resize_keyboard=True)

# chat controls shown during anonymous chat
chat_actions_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="❌ پایان چت"), KeyboardButton(text="🚩 گزارش"), KeyboardButton(text="⛔ بلاک")],
    ],
    resize_keyboard=True
)

# start chat options
start_chat_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔎 جستجوی رندوم")],
        [KeyboardButton(text="🔎 جستجو با فیلتر")],
        [KeyboardButton(text="📋 لیست آنلاین")]
    ],
    resize_keyboard=True
)

# inline buttons for online list: created dynamically in handlers
def invite_request_buttons(requester_id: int):
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton(text="قبول درخواست", callback_data=f"accept_req_{requester_id}"))
    kb.add(InlineKeyboardButton(text="رد درخواست", callback_data=f"decline_req_{requester_id}"))
    return kb
