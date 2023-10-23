from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
import time
from datetime import datetime, timedelta, time
from aiogram_calendar import simple_cal_callback

from aiogram.dispatcher.filters import Text
from aiogram_calendar import SimpleCalendar

from create_bot import scheduler
from aiogram_timepicker.panel import FullTimePicker, full_timep_callback

from keyboards.kb_client import loop_kb, post_formatting_kb, change_create_post_kb, change_post_kb, planning_kb
from utils import send_message_time, send_message_cron


async def choose_loop_time(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    data = await state.get_data()
    job_id = data.get('job_id')
    if job_id:
        data = scheduler.get_job(job_id).kwargs['data']
    keys_to_check = ['post_text', 'loaded_post_files', 'voice', 'video_note', 'random_photos_number',
                     'random_videos_number']
    if any(data.get(key) for key in keys_to_check):
        from handlers.client import FSMClient

        await FSMClient.time_loop.set()
        await call.message.answer(text="Ваша публікація буде опублікована кожного дня в обраний час: ",
                                  reply_markup=await FullTimePicker().start_picker())
    else:
        await call.message.answer(text='❌ Ви не можете зациклити пост, так як у ньому немає контенту.\n'
                                       'Наповніть пост текстом або медіа:',
                                  reply_markup=loop_kb)





async def full_picker_handler(callback_query: types.CallbackQuery, callback_data: dict, state: FSMContext):
    r = await FullTimePicker().process_selection(callback_query, callback_data)
    s = await state.get_state()
    fsm_data = await state.get_data()
    job_id = fsm_data.get('job_id')

    if callback_data['act'] == 'CANCEL':
        await state.reset_state(with_data=False)
        if callback_query.message.text == 'Будь ласка оберіть час:':
            await nav_cal_handler(callback_query, state)

    await callback_query.answer()
    if r.selected:
        if s == 'FSMClient:time_planning':
            await state.update_data(time_planning=r.time)
            data = await state.get_data()
            selected_time: time = data.get("time_planning")
            selected_date: datetime = data.get("date_planning")
            selected_date = selected_date.replace(hour=selected_time.hour, minute=selected_time.minute)

            selected_time_str = r.time.strftime("%H:%M")
            selected_date_str = data.get("date_planning").strftime("%d/%m/%Y")

            if job_id:
                job = scheduler.get_job(job_id)
                job.reschedule(trigger='date', run_date=selected_date)
                await callback_query.message.answer(
                    f'Планування змінено на {selected_time_str} - {selected_date_str}',
                    reply_markup=post_formatting_kb)
            else:
                await callback_query.message.answer(
                    f'Публікацію заплановано на {selected_time_str} - {selected_date_str}',
                    reply_markup=change_create_post_kb)

                await callback_query.message.delete_reply_markup()
                scheduler.add_job(send_message_time, trigger='date', run_date=selected_date,
                                  kwargs={'data': data, 'callback_query': callback_query})

        elif s == 'FSMClient:time_loop':
            await state.update_data(time_loop=r.time)
            data = await state.get_data()
            selected_time_str = r.time.strftime("%H:%M")
            minutes_to_add = timedelta(minutes=4)
            selected_time_str_4min = (r.datetime + minutes_to_add).strftime("%H:%M")
            if job_id:
                job = scheduler.get_job(job_id)
                job.reschedule(trigger='cron', hour=r.time.hour, minute=r.time.minute)
                await callback_query.message.answer(
                    f'Змінено: публікація щодня в діапазоні {selected_time_str} - {selected_time_str_4min}',
                    reply_markup=change_create_post_kb
                )
            else:
                await callback_query.message.answer(
                    f'Пост буде публікуватись щодня в діапазоні {selected_time_str} - {selected_time_str_4min}',
                    reply_markup=change_create_post_kb
                )
                scheduler.add_job(send_message_cron, trigger='cron', hour=r.time.hour, minute=r.time.minute,
                                  kwargs={'data': data, 'callback_query': callback_query})

        await state.reset_state(with_data=False)


async def process_simple_calendar(callback_query: types.CallbackQuery, callback_data: dict, state: FSMContext):
    await callback_query.answer()
    selected, date = await SimpleCalendar().process_selection(callback_query, callback_data)
    if selected:
        await state.update_data(date_planning=date)
        await callback_query.message.answer(
            text=f'Ви обрали: {date.strftime("%d/%m/%Y")}'
        )
        await state.reset_state(with_data=False)
        from handlers.client import FSMClient
        await FSMClient.time_planning.set()
        await callback_query.message.answer(
            "Будь ласка оберіть час: ",
            reply_markup=await FullTimePicker().start_picker()
        )


async def choose_plan_date(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    fsm_data = await state.get_data()
    keys_to_check = ['post_text', 'loaded_post_files', 'voice', 'video_note', 'random_photos_number',
                     'random_videos_number']
    job_id = fsm_data.get('job_id')
    if job_id:
        fsm_data = scheduler.get_job(job_id).kwargs['data']

    if any(fsm_data.get(key) for key in keys_to_check):
        from handlers.client import FSMClient
        await FSMClient.date_planning.set()
        await call.message.answer(text="Оберіть дату: ", reply_markup=await SimpleCalendar().start_calendar())
        await call.answer()
    else:
        await call.message.answer(text='❌ Ви не можете запланувати пост, так як у ньому немає контенту.\n'
                                       'Наповніть пост текстом або медіа:',
                                  reply_markup=planning_kb)


async def post_looping(call, state: FSMContext):
    await state.update_data(post_type='looped')
    if isinstance(call, types.CallbackQuery):
        await call.answer()
        await call.message.edit_text(text='Оберіть варіант:', reply_markup=loop_kb)
    else:
        await call.answer(text='Оберіть варіант:', reply_markup=loop_kb)


async def nav_cal_handler(call, state: FSMContext):
    await state.update_data(post_type='planned')
    if isinstance(call, types.CallbackQuery):
        await call.answer()
        if call.data == 'full_timepicker:CANCEL:-1:-1:-1':
            await call.message.answer(text='Оберіть варіант:', reply_markup=planning_kb)
        else:
            try:
                await call.message.edit_text(text='Оберіть варіант:', reply_markup=planning_kb)
            except:
                pass
    else:
        await call.answer(text='Оберіть варіант:', reply_markup=planning_kb)


def register_handlers_schedule(dp: Dispatcher):
    dp.register_callback_query_handler(nav_cal_handler, Text(equals='Запланувати'))
    dp.register_callback_query_handler(choose_plan_date, Text(equals='choose_date'))
    dp.register_callback_query_handler(choose_loop_time, Text(equals='choose_loop_time'))
    from handlers.client import FSMClient
    dp.register_callback_query_handler(process_simple_calendar, simple_cal_callback.filter(),
                                       state=FSMClient.date_planning)
    dp.register_callback_query_handler(full_picker_handler, full_timep_callback.filter(), state=FSMClient.time_planning)
    dp.register_callback_query_handler(full_picker_handler, full_timep_callback.filter(), state=FSMClient.time_loop)

    dp.register_callback_query_handler(post_looping, Text(equals='Зациклити'))
