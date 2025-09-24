import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import TOKEN, PROXY_HEALTH_INTERVAL
from handlers import start, download, music, admin, admin_panel, anonymous_chat
from services.proxy_service import proxy_health_worker, init_proxy_service
from services.database import init_db

async def main():
    init_db()
    init_proxy_service()
    bot = Bot(token=TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(start.router)
    dp.include_router(download.router)
    dp.include_router(music.router)
    dp.include_router(admin.router)
    dp.include_router(admin_panel.router)
    dp.include_router(anonymous_chat.router)

    asyncio.create_task(proxy_health_worker())

    print("bot is running")
    await dp.start_polling(bot)
    
if __name__=="__main__":
   asyncio.run(main())
