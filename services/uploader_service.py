import requests
import os

import os

GOOGLE_DRIVE_TOKEN = os.getenv("GOOGLE_DRIVE_TOKEN", "TOKEN")
DROPBOX_TOKEN = os.getenv("DROPBOX_TOKEN", "TOKEN")

async def upload_file(file_path: str) -> str:
    """
    تلاش برای آپلود روی:
    1. Google Drive
    2. Dropbox
    3. gofile.io
    توجه: توکن‌ها باید بعداً تنظیم شوند!
    """
    try:
        return upload_google_drive(file_path)
    except Exception as e:
        # print یا لاگ خطا برای عیب‌یابی
        try:
            return upload_dropbox(file_path)
        except Exception as e:
            try:
                return upload_gofile(file_path)
            except Exception as e:
                return "آپلود فایل موفق نبود. لطفاً بعداً دوباره تلاش کنید."

def upload_google_drive(file_path: str) -> str:
    """آپلود در گوگل درایو (نیاز به توکن معتبر دارد)"""
    headers = {"Authorization": f"Bearer {GOOGLE_DRIVE_TOKEN}"}
    metadata = {"name": os.path.basename(file_path)}
    files = {
        "data": ("metadata", str(metadata), "application/json"),
        "file": open(file_path, "rb")
    }
    try:
        response = requests.post(
            "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart",
            headers=headers, files=files
        )
    finally:
        files["file"].close()
    if response.status_code != 200:
        raise Exception("GOOGLE DRIVE UPLOAD FAILED")
    file_id = response.json()["id"]
    return f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"

def upload_dropbox(file_path: str) -> str:
    """آپلود در دراپ‌باکس (نیاز به توکن معتبر دارد)"""
    headers = {
        "Authorization": f"Bearer {DROPBOX_TOKEN}",  # اصلاح تایپ Athorization
        "Dropbox-API-Arg": f'{{"path": "/{os.path.basename(file_path)}","mode":"add","autorename":true,"mute":false}}',
        "Content-Type": "application/octet-stream",
    }
    with open(file_path, "rb") as f:
        response = requests.post(
            "https://content.dropboxapi.com/2/files/upload",
            headers=headers,
            data=f
        )
    if response.status_code != 200:
        raise Exception("DROPBOX UPLOAD FAILED")
    return f"https://www.dropbox.com/home/{os.path.basename(file_path)}"

def upload_gofile(file_path: str) -> str:
    """آپلود در gofile.io (بدون نیاز به اکانت)"""
    with open(file_path, "rb") as f:
        files = {"file": f}
        response = requests.post("https://store1.gofile.io/uploadFile", files=files)
    if response.status_code != 200:
        raise Exception("GOFILE UPLOAD FAILED")
    return response.json()["data"]["downloadPage"]









