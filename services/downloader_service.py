import asyncio
import yt_dlp
from pathlib import Path
from services.proxy_service import get_active_proxies, mark_proxy_failed, test_proxy
from services.database import get_user_cookie_path
from services.crypto import decrypt_cookie_to_temp, remove_temp_cookie

DOWNLOAD_DIR = Path("data/downloads")
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

def get_formats(url: str):
    """
    فراخوانی همزمان (blocking) برای گرفتن فرمت‌ها با yt-dlp
    """
    ydl_opts = {}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        formats = []
        for f in info.get("formats", []):
            if f.get("vcodec") == "none":
                continue
            formats.append({
                "format_id": f.get("format_id"),
                "resolution": f.get("resolution") or f.get("height") or "NA",
                "ext": f.get("ext"),
                "filesize": f.get("filesize") or f.get("filesize_approx") or 0
            })
        formats.sort(key=lambda x: int(x.get("resolution") or 0), reverse=True)
        return formats

async def download_no_proxy(url: str, format_id: str = None, tg_user_id: int = None):
    ydl_opts = {
        'outtmpl': str(DOWNLOAD_DIR / '%(title)s.%(ext)s'),
        'format': format_id or 'best',
        'nocheckcertificate': True,
        'no_warnings': True,
    }
    temp_cookie = None
    if tg_user_id:
        enc_path = get_user_cookie_path(tg_user_id)
        if enc_path:
            temp_cookie = decrypt_cookie_to_temp(enc_path, tg_user_id)
            ydl_opts['cookiefile'] = temp_cookie

    def run():
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
            return filename
        finally:
            if temp_cookie:
                remove_temp_cookie(temp_cookie)

    fn = await asyncio.to_thread(run)
    return fn

async def try_download_with_proxy(url: str, proxy: str, format_id: str = None, tg_user_id: int = None):
    ydl_opts = {
        'outtmpl': str(DOWNLOAD_DIR / '%(title)s.%(ext)s'),
        'format': format_id or 'best',
        'proxy': proxy,
        'nocheckcertificate': True,
        'no_warnings': True,
    }
    temp_cookie = None
    if tg_user_id:
        enc_path = get_user_cookie_path(tg_user_id)
        if enc_path:
            temp_cookie = decrypt_cookie_to_temp(enc_path, tg_user_id)
            ydl_opts['cookiefile'] = temp_cookie

    def run():
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
            return filename
        finally:
            if temp_cookie:
                remove_temp_cookie(temp_cookie)

    fn = await asyncio.to_thread(run)
    return fn

async def download_with_proxy_rotation(url: str, format_id: str = None, tg_user_id: int = None, max_tries: int = None):
    """
    سعی می‌کند پروکسی‌های فعال را یکی‌یکی امتحان کند. اگر همه شکست خورد، بدون پروکسی دانلود می‌کند.
    """
    max_tries = max_tries or 6
    proxies = get_active_proxies(limit=max_tries*2)
    tried = 0
    for p in proxies:
        if tried >= max_tries:
            break
        tried += 1
        try:
            ok = test_proxy(p, timeout=6)
            if not ok:
                mark_proxy_failed(p)
                continue
            filename = await try_download_with_proxy(url, p, format_id=format_id, tg_user_id=tg_user_id)
            return filename
        except Exception:
            mark_proxy_failed(p)
            continue
    # اگر هیچ پروکسی نشد، بدون پروکسی دانلود کن
    return await download_no_proxy(url, format_id=format_id, tg_user_id=tg_user_id)