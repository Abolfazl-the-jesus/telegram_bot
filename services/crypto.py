from cryptography.fernet import Fernet
from pathlib import Path
from config import DATA_DIR
import uuid

KEY_FILE = DATA_DIR / "secret.key"
COOKIES_DIR = DATA_DIR / "cookies"
COOKIES_DIR.mkdir(parents=True, exist_ok=True)

def _get_key():
    if not KEY_FILE.exists():
        key = Fernet.generate_key()
        KEY_FILE.write_bytes(key)
    else:
        key = KEY_FILE.read_bytes()
    return key

def encrypt_and_store_cookie(src_path: str, user_id: int) -> str:
    """
    رمزگذاری و ذخیره کوکی به صورت امن با حذف فایل اصلی
    """
    key = _get_key()
    f = Fernet(key)
    data = Path(src_path).read_bytes()
    token = f.encrypt(data)
    dest = COOKIES_DIR / f"{user_id}_cookies.enc"
    dest.write_bytes(token)
    try:
        Path(src_path).unlink()
    except Exception as e:
        print(f"خطا در حذف فایل اصلی کوکی: {e}")
    return str(dest)

def decrypt_cookie_to_temp(enc_path: str, user_id: int) -> str:
    """
    رمزگشایی و استخراج موقت کوکی برای دانلود. از uuid برای جلوگیری از تداخل فایل موقت استفاده می‌کند.
    """
    key = _get_key()
    f = Fernet(key)
    data = Path(enc_path).read_bytes()
    dec = f.decrypt(data)
    tmp_path = COOKIES_DIR / f"{user_id}_{uuid.uuid4().hex}_cookies.tmp.txt"
    tmp_path.write_bytes(dec)
    return str(tmp_path)

def remove_temp_cookie(tmp_path: str):
    """
    حذف فایل موقت کوکی (در صورت وجود)
    """
    try:
        Path(tmp_path).unlink()
    except Exception as e:
        print(f"خطا در حذف فایل موقت کوکی: {e}")