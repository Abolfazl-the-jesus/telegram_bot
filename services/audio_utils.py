import os
import yt_dlp
from pydub import AudioSegment
import asyncio

DOWNLOAD_PATH = "downloads"

async def download_audio(link: str, filename: str = "temp.mp3") -> str:
    """
    دانلود صدا از لینک (یوتیوب یا هر پلتفرمی که yt-dlp ساپورت کنه).
    """
    if not os.path.exists(DOWNLOAD_PATH):
        os.makedirs(DOWNLOAD_PATH)

    output_path = os.path.join(DOWNLOAD_PATH, filename)

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_path,
        "quiet": True,
    }

    def run():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([link])
    await asyncio.to_thread(run)
    return output_path

async def convert_to_wav(input_path: str, output_name: str = None) -> str:
    """
    تبدیل mp3 به wav برای پردازش اثر انگشت.
    """
    if output_name is None:
        output_name = f"{os.path.splitext(os.path.basename(input_path))[0]}.wav"
    output_path = os.path.join(DOWNLOAD_PATH, output_name)

    def convert():
        sound = AudioSegment.from_file(input_path)
        sound.export(output_path, format="wav")
    await asyncio.to_thread(convert)
    return output_path