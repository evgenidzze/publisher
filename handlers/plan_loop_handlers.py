from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
import time
from datetime import datetime, timedelta, time
from aiogram_calendar import simple_cal_callback

from aiogram.dispatcher.filters import Text
from aiogram_calendar import SimpleCalendar

from create_bot import scheduler
from aiogram_timepicker.panel import FullTimePicker, full_timep_callback

from keyboards.kb_client import post_formatting_kb, change_create_post_kb, media_kb, \
    plan_menu_kb
from utils import send_message_time, send_message_cron


async def plan_menu(call: types.CallbackQuery, state: FSMContext):
    fsm_data = await state.get_data()
    keys_to_check = ['post_text', 'loaded_post_files', 'voice', 'video_note', 'random_photos_number',
                     'random_videos_number']
    job_id = fsm_data.get('job_id')
    if job_id:
        fsm_data = scheduler.get_job(job_id).kwargs['data']

    if any(fsm_data.get(key) for key in keys_to_check):
        await call.message.edit_text(text='Бажаєте зациклити чи запланувати пост?\n\n'
                                          '<i>🗓 - При плануванні, пост опублікується 1 раз в обрану дату та час.\n\n'
                                          '🌀 - При зацикленні, пост буде публікуватись кожного дня в обраний час з '
                                          'різницею від 0хв до 4хв.</i>',
                                     parse_mode='html', reply_markup=plan_menu_kb)
    else:
        try:
            from handlers.client import FSMClient
            await FSMClient.media_answer.set()

            await call.message.edit_text(text='❌ Ви не можете планувати пост, так як у ньому немає контенту.\n'
                                              'Наповніть пост текстом або медіа:',
                                         reply_markup=media_kb)
        except:
            pass


async def choose_loop_time(call: types.CallbackQuery, state: FSMContext):
    from handlers.client import FSMClient
    await call.answer()
    data = await state.get_data()
    job_id = data.get('job_id')
    if job_id:
        job = scheduler.get_job(job_id)
        data = job.kwargs.get('data')
        data['post_type'] = 'looped'
        job.modify(kwargs={'data': data})
    else:
        await state.update_data(post_type='looped')

    await FSMClient.time_loop.set()
    await call.message.answer(text="Ваша публікація буде опублікована кожного дня в обраний час: ",
                              reply_markup=await FullTimePicker().start_picker())


async def full_picker_handler(callback_query: types.CallbackQuery, callback_data: dict, state: FSMContext):
    await callback_query.answer()
    r = await FullTimePicker().process_selection(callback_query, callback_data)
    s = await state.get_state()
    fsm_data = await state.get_data()
    job_id = fsm_data.get('job_id')

    if callback_data['act'] == 'CANCEL':
        await state.reset_state(with_data=False)
        from handlers.client import formatting_main_menu
        await formatting_main_menu(callback_query, state)

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
                                  kwargs={'data': data})

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
                                  kwargs={'data': data})

        await state.reset_state(with_data=False)


async def process_simple_calendar(callback_query: types.CallbackQuery, callback_data: dict, state: FSMContext):
    from handlers.client import FSMClient
    await callback_query.answer()
    selected, date = await SimpleCalendar().process_selection(callback_query, callback_data)
    if selected:
        await state.update_data(date_planning=date)
        await callback_query.message.answer(
            text=f'Ви обрали: {date.strftime("%d/%m/%Y")}'
        )
        await state.reset_state(with_data=False)
        await FSMClient.time_planning.set()
        await callback_query.message.answer(
            "Будь ласка оберіть час: ",
            reply_markup=await FullTimePicker().start_picker()
        )


async def choose_plan_date(call: types.CallbackQuery, state: FSMContext):
    from handlers.client import FSMClient
    await call.answer()
    data = await state.get_data()
    job_id = data.get('job_id')

    if job_id:
        job = scheduler.get_job(job_id)
        data = job.kwargs.get('data')
        data['post_type'] = 'planned'
        job.modify(kwargs={'data': data})
    else:
        await state.update_data(post_type='planned')

    await FSMClient.date_planning.set()
    await call.message.answer(text="Оберіть дату: ", reply_markup=await SimpleCalendar().start_calendar())
    await call.answer()


def register_handlers_schedule(dp: Dispatcher):
    dp.register_callback_query_handler(plan_menu, Text(equals='Планування'))
    dp.register_callback_query_handler(choose_plan_date, Text(equals='Запланувати'))
    dp.register_callback_query_handler(choose_loop_time, Text(equals='Зациклити'))
    from handlers.client import FSMClient
    dp.register_callback_query_handler(process_simple_calendar, simple_cal_callback.filter(),
                                       state=FSMClient.date_planning)
    dp.register_callback_query_handler(full_picker_handler, full_timep_callback.filter(), state=FSMClient.time_planning)
    dp.register_callback_query_handler(full_picker_handler, full_timep_callback.filter(), state=FSMClient.time_loop)

