from aiogram import Router, types
from aiogram.filters import Command
from services.proxy_service import add_proxy, remove_proxy, list_proxies, extract_proxies_from_text, quarantine_proxy
from config import ADMINS

router = Router()

def is_admin(user_id: int) -> bool:
    return user_id in ADMINS

@router.message(Command("addproxy"))
async def cmd_addproxy(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.reply("❌ شما ادمین نیستید.")
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return await message.reply("Usage: /addproxy <proxy>")
    proxy = parts[1].strip()
    ok = add_proxy(proxy)
    if ok:
        await message.reply(f"✅ پروکسی اضافه شد: {proxy}")
    else:
        await message.reply(f"ℹ️ پروکسی قبلاً وجود دارد یا نامعتبر: {proxy}")

@router.message(Command("delproxy"))
async def cmd_delproxy(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.reply("❌ شما ادمین نیستید.")
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return await message.reply("Usage: /delproxy <proxy>")
    proxy = parts[1].strip()
    remove_proxy(proxy)
    await message.reply(f"✅ پروکسی حذف شد: {proxy}")

@router.message(Command("listproxies"))
async def cmd_listproxies(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.reply("❌ شما ادمین نیستید.")
    rows = list_proxies()
    if not rows:
        return await message.reply("لیست پروکسی خالی است.")
    text = "آیدی | پروکسی | فعال | شکست‌ها\n"
    text += "\n".join([f"{r[0]} | {r[1]} | {r[4]} | {r[5]}" for r in rows])  # indexها اصلاح شد
    await message.reply(text)

@router.message(Command("submitproxy"))
async def cmd_submitproxy(message: types.Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return await message.reply("Usage: /submitproxy <proxy or text containing proxy>")
    text = parts[1]
    proxies = extract_proxies_from_text(text)
    if not proxies:
        return await message.reply("هیچ پروکسی معتبری پیدا نشد در متنت.")
    added = []
    for p in proxies:
        quarantine_proxy(p)
        added.append(p)
    await message.reply(f"✅ درخواست ثبت انجام شد. پروکسی‌ها به quarantine اضافه شدند:\n" + "\n".join(added))

@router.message()
async def handle_forwarded(message: types.Message):
    if message.forward_from or message.forward_from_chat:
        text = message.text or ""
        proxies = extract_proxies_from_text(text)
        if proxies:
            if is_admin(message.from_user.id):
                added = []
                for p in proxies:
                    if add_proxy(p):
                        added.append(p)
                if added:
                    return await message.reply("✅ پروکسی‌های اضافه شده:\n" + "\n".join(added))
                else:
                    return await message.reply("هیچ پروکسی جدیدی اضافه نشد (ممکن است قبلاً اضافه شده باشند).")
            else:
                for p in proxies:
                    quarantine_proxy(p)
                return await message.reply("✅ پروکسی‌ها دریافت شد و برای تست به quarantine اضافه شدند. ادمین‌ها بعداً تایید/فعال خواهند کرد.")