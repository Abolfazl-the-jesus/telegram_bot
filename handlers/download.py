
from aiogram import Router, types
from aiogram.types import Message, InputFile, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.filters import Command
from services.downloader_service import download_no_proxy as download_video, get_formats
from services.database import get_user_best_quality, set_user_best_quality
from services.uploader_service import upload_file
import os

router = Router()
MAX_SIZE_MB = 1900

@router.message(Command("download"))
async def cmd_download(message: Message):
    await message.answer("لینک را ارسال کنید.")

@router.message()
async def handle_link(message: Message):
    url = message.text.strip()
    await message.answer("در حال آماده‌سازی ...")

    try:
        if "youtube.com" in url or "youtu.be" in url:
            formats = get_formats(url)
            user_best = await get_user_best_quality(message.from_user.id)
            if user_best:
                file_path = await download_video(url, format_id=user_best, tg_user_id=message.from_user.id)
                await send_file(message, file_path)
                return
            if len(formats) == 1:
                file_path = await download_video(url, format_id=formats[0]['format_id'], tg_user_id=message.from_user.id)
                await send_file(message, file_path)
            else:
                kb = InlineKeyboardMarkup(row_width=2)
                for f in formats:
                    kb.add(
                        InlineKeyboardButton(
                            text=f"{f['resolution']}p",
                            callback_data=f"dl_{f['format_id']}_{url}"
                        )
                    )
                await message.answer("کیفیت مورد نظر را انتخاب کنید", reply_markup=kb)
        else:
            file_path = await download_video(url, tg_user_id=message.from_user.id)
            await send_file(message, file_path)
    except Exception as e:
        await message.answer(f"خطا:\n{e}")

@router.callback_query()
async def handle_quality_choice(callback: CallbackQuery):
    data = callback.data
    await callback.answer()
    if data.startswith("dl_"):
        _, format_id, url = data.split("_", 2)
        await callback.message.answer("دانلود با کیفیت انتخاب شده ...")
        file_path = await download_video(url, format_id=format_id, tg_user_id=callback.from_user.id)
        await send_file(callback.message, file_path)
    elif data.startswith("best_"):
        _, best_format, url = data.split("_", 2)
        await set_user_best_quality(callback.from_user.id, best_format)
        await callback.message.answer("تنظیم شد: همیشه بهترین کیفیت دانلود شود")
        file_path = await download_video(url, format_id=best_format, tg_user_id=callback.from_user.id)
        await send_file(callback.message, file_path)

async def send_file(message: Message, file_path: str):
    """بررسی حجم فایل و ارسال مستقیم یا آپلود ابری"""
    size_mb = os.path.getsize(file_path) / (1024 * 1024)
    if size_mb <= MAX_SIZE_MB:
        await message.answer_document(InputFile(file_path))
    else:
        await message.answer("در حال آپلود روی سرورهای ابری ...")
        link = await upload_file(file_path)
        await message.answer(f"لینک دانلود:\n{link}")



