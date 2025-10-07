import re
import requests
from typing import List
from config import PROXY_HEALTH_INTERVAL
import asyncio
from services.database import (
    add_proxy_to_db, remove_proxy_from_db, list_proxies_from_db,
    get_active_proxies_from_db, mark_proxy_failed_in_db, mark_proxy_ok_in_db,
    quarantine_proxy_in_db
)

PROXY_REGEX = re.compile(r'((?:socks5|socks4|http|https)://[^\s,;]+|[0-9]{1,3}(?:\.[0-9]{1,3}){3}:\d{2,5})')

TEST_URL = "https://www.google.com/generate_204"
REQUEST_TIMEOUT = 8

def extract_proxies_from_text(text: str) -> List[str]:
    found = PROXY_REGEX.findall(text or "")
    normalized = []
    for s in found:
        if "://" not in s:
            s = "http://" + s
        normalized.append(s)
    return normalized

async def add_proxy(proxy: str) -> bool:
    return await add_proxy_to_db(proxy)

async def remove_proxy(proxy: str):
    return await remove_proxy_from_db(proxy)

async def quarantine_proxy(proxy: str):
    return await quarantine_proxy_in_db(proxy)

async def list_proxies(limit: int = 100):
    return await list_proxies_from_db(limit)

async def get_active_proxies(limit: int = 50):
    return await get_active_proxies_from_db(limit)

async def mark_proxy_failed(proxy: str):
    await mark_proxy_failed_in_db(proxy)

async def mark_proxy_ok(proxy: str):
    await mark_proxy_ok_in_db(proxy)

def test_proxy(proxy: str, timeout: int = REQUEST_TIMEOUT) -> bool:
    proxies = {"http": proxy, "https": proxy}
    try:
        r = requests.get(TEST_URL, proxies=proxies, timeout=timeout)
        if 200 <= r.status_code < 400:
            mark_proxy_ok(proxy)
            return True
    except Exception:
        mark_proxy_failed(proxy)
        return False
    mark_proxy_failed(proxy)
    return False

async def proxy_health_worker():
    """
    پروسه پس‌زمینه که دوره‌ای پروکسی‌های quarantine و inactive را تست می‌کند و وضعیت activeها را هم به‌روزرسانی می‌کند.
    """
    while True:
        try:
            rows = await list_proxies_from_db(limit=500)
            for row in rows:
                proxy = row[1]
                test_proxy(proxy)
        except Exception as e:
            print("proxy_health_worker error:", e)
        await asyncio.sleep(PROXY_HEALTH_INTERVAL)