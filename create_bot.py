from aiogram import Bot, Dispatcher
from config import TOKEN_API
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler(timezone='Europe/Kiev')
storage = MemoryStorage()
scheduler.start()

bot = Bot(TOKEN_API)
dp = Dispatcher(bot, storage=storage)



