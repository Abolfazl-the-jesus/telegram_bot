from aiogram import Router, types
from config import ADMINS

router = Router()

@router.message(lambda msg: msg.text == "admin_panel")
async def admin_panel(message: types.Message):
    if message.from_user.id not in ADMINS:
        return await message.answer("شما ادمین نیستید.")
    await message.answer(
        "🎛 وارد پنل ادمین شدید!\nدستورات:\n/addproxy ...\n/delproxy ...\n/listproxies ...\nیا از دستورات ادمین استفاده کنید."
    )