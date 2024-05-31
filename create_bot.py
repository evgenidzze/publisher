from aiogram import Bot, Dispatcher
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler_di import ContextSchedulerDecorator

from config import TOKEN_API
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import os
os.environ['TZ'] = 'Europe/Kyiv'

job_stores = {
    "default": RedisJobStore(
        jobs_key="dispatched_trips_jobs", run_times_key="dispatched_trips_running",
        host="localhost", port=6379
    )
}


scheduler = ContextSchedulerDecorator(AsyncIOScheduler(jobstores=job_stores))
storage = MemoryStorage()
scheduler.start()

bot = Bot(TOKEN_API)
dp = Dispatcher(bot, storage=storage)



