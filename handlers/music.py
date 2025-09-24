from aiogram import Router, types
from services.audio_utils import download_audio, convert_to_wav
from services.music_recognition import recognize_song
from services.search_music import search_musicbrainz, search_lastfm
from config import LASTFM_API_KEY
import os
import uuid

router = Router()
DOWNLOAD_PATH = "downloads"

@router.message(lambda msg: msg.text == "پیدا کردن موزیک" or msg.text == "/findsong")
async def music_entry(message: types.Message):
    await message.answer("لطفاً لینک یا فایل صوتی موزیک مورد نظرت رو ارسال کن.")

@router.message(lambda msg: msg.audio or msg.voice or (msg.text and msg.text.startswith("http")))
async def find_song(message: types.Message):
    file_path = None

    # اگر لینک داده
    if message.text and message.text.startswith("http"):
        unique_name = f"{uuid.uuid4().hex}.mp3"
        try:
            file_path = await download_audio(message.text, unique_name)
        except Exception as e:
            await message.answer(f"❌ خطا در دانلود: {e}")
            return

    # اگر فایل صوتی فرستاده
    elif message.audio or message.voice:
        file = message.audio or message.voice
        file_id = file.file_id
        file_name = f"{file_id}.mp3"
        file_path = os.path.join(DOWNLOAD_PATH, file_name)
        os.makedirs(DOWNLOAD_PATH, exist_ok=True)
        await message.bot.download(file, file_path)
    else:
        await message.answer("❌ لطفاً یا لینک بده یا فایل صوتی ارسال کن.")
        return

    # تبدیل به wav
    try:
        wav_path = await convert_to_wav(file_path)
    except Exception as e:
        await message.answer(f"خطا در تبدیل به wav: {e}")
        return

    # شناسایی آهنگ با Shazamio
    try:
        recognized = await recognize_song(wav_path)
    except Exception as e:
        await message.answer(f"خطا در شناسایی موزیک: {e}")
        return

    if recognized and recognized.get("title"):
        title = recognized["title"]
        artist = recognized.get("artist", "")
        # نمایش نتیجه شناسایی اولیه
        await message.answer(f"🎶 شناسایی شد:\nنام: {title}\nخواننده: {artist}\n{recognized.get('url','')}")
        # جستجو در دیتابیس‌ها
        result_mb = await search_musicbrainz(title, artist)
        result_lastfm = await search_lastfm(LASTFM_API_KEY, title, artist)

        if result_mb:
            await message.answer(
                f"📀 MusicBrainz:\n"
                f"نام: {result_mb['title']}\n"
                f"خواننده: {result_mb['artist']}"
            )
        elif result_lastfm:
            await message.answer(
                f"📀 Last.fm:\n"
                f"نام: {result_lastfm['title']}\n"
                f"خواننده: {result_lastfm['artist']}\n"
                f"لینک: {result_lastfm['url']}"
            )
        else:
            await message.answer("⚠️ آهنگ توی دیتابیس‌های رایگان پیدا نشد.")
    else:
        await message.answer("❌ متأسفم! نتونستم آهنگ رو شناسایی کنم.")