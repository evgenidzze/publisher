import logging

from aiogram.utils import executor

from create_bot import dp
from handlers import client, admin, plan_loop_handlers, catalog_handlers, signals

admin.register_handlers_admin(dp)
client.register_handlers_client(dp)
plan_loop_handlers.register_handlers_schedule(dp)
catalog_handlers.register_handlers_catalog(dp)
signals.register_handlers_client(dp)


logging.basicConfig(level=logging.INFO)
executor.start_polling(dp, skip_updates=True)
