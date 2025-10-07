from aiogram import Router, types
from config import ADMINS
from services.database import list_reports

router = Router()

@router.message(lambda msg: msg.text == "admin_panel")
async def admin_panel(message: types.Message):
    if message.from_user.id not in ADMINS:
        return await message.answer("شما ادمین نیستید.")
    await message.answer(
        "🎛 وارد پنل ادمین شدید!\nدستورات:\n/addproxy ...\n/delproxy ...\n/listproxies ...\n/reports"
    )

@router.message(lambda msg: msg.text == "/reports")
async def admin_reports(message: types.Message):
    if message.from_user.id not in ADMINS:
        return await message.answer("شما ادمین نیستید.")
    rows = await list_reports(limit=30)
    if not rows:
        return await message.answer("هیچ گزارشی نیست.")
    text = "\n".join([f"#{r['id']} {r['reporter_id']} -> {r['reported_id']} : {r['reason'] or ''}" for r in rows])
    await message.answer(text)