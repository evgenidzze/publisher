import logging

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
import time
from datetime import datetime, timedelta, time

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram_calendar import simple_cal_callback

from aiogram.dispatcher.filters import Text
from aiogram_calendar import SimpleCalendar

from create_bot import scheduler
from aiogram_timepicker.panel import FullTimePicker, full_timep_callback

from handlers.client import number_of_random_videos, number_of_random_photos, FSMClient
from keyboards.kb_client import post_formatting_kb, change_create_post_kb, media_kb, \
    plan_menu_kb, back_to_plan_menu, back
from utils import send_message_time, send_message_cron, send_v_notes_cron


async def plan_menu(call: types.CallbackQuery, state: FSMContext):
    await state.reset_state(with_data=False)
    fsm_data = await state.get_data()
    keys_to_check = ['post_text', 'loaded_post_files', 'voice', 'video_note', 'random_photos_number',
                     'random_videos_number', 'random_v_notes_id', 'random_gifs_number']
    job_id = fsm_data.get('job_id')
    if job_id:
        job = scheduler.get_job(job_id)
        if job.kwargs:
            fsm_data = job.kwargs['data']
    if any(fsm_data.get(key) for key in keys_to_check):
        try:
            await call.message.edit_text(text='Бажаєте зациклити чи запланувати пост?\n\n'
                                              '<i>🗓 - При плануванні, пост опублікується 1 раз в обрану дату та час.\n\n'
                                              '🌀 - При зацикленні, пост буде публікуватись кожного дня в обраний час з '
                                              'різницею від 0хв до 4хв.</i>',
                                         parse_mode='html', reply_markup=plan_menu_kb)
        except:
            await call.message.answer(text='Бажаєте зациклити чи запланувати пост?\n\n'
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


# async def choose_loop_time(message: types.Message, state: FSMContext):
#     from handlers.client import FSMClient
#     data = await state.get_data()
#     job_id = data.get('job_id')
#     if job_id:
#         job = scheduler.get_job(job_id)
#         data = job.kwargs.get('data')
#         data['post_type'] = 'looped'
#         data['skip_days_loop'] = message.text
#         job.modify(kwargs={'data': data})
#     else:
#         await state.update_data(post_type='looped')
#         await state.update_data(skip_days_loop=message.text)
#
#     await FSMClient.time_loop.set()
#     await message.answer(text="Ваша публікація буде опублікована кожного дня в обраний час: ",
#                          reply_markup=await FullTimePicker().start_picker())


async def process_simple_calendar(callback_query: types.CallbackQuery, callback_data: dict, state: FSMContext):
    from handlers.client import FSMClient
    await callback_query.answer()
    selected, date = await SimpleCalendar().process_selection(callback_query, callback_data)
    if selected:
        await state.update_data(date_planning=date)
        await state.reset_state(with_data=False)
        await FSMClient.time_planning.set()
        await callback_query.message.edit_text(
            f'Ви обрали: {date.strftime("%d/%m/%Y")}\n'
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
    await call.message.edit_text(text="Оберіть дату: ", reply_markup=await SimpleCalendar().start_calendar())


async def enter_start_loop_date(call: types.CallbackQuery, state: FSMContext):
    from handlers.client import FSMClient
    await call.answer()

    await FSMClient.start_loop_date.set()
    await call.message.edit_text(text='З якого числа почати розсилку?',
                                 reply_markup=await SimpleCalendar().start_calendar())


async def load_start_date_enter_time(callback_query: types.CallbackQuery, callback_data: dict, state: FSMContext):
    from handlers.client import FSMClient
    selected, date = await SimpleCalendar().process_selection(callback_query, callback_data)
    if selected:
        data = await state.get_data()
        job_id = data.get('job_id')
        if job_id:
            job = scheduler.get_job(job_id)
            job_data = job.kwargs.get('data')
            job_data['start_loop_date'] = date
        else:
            await state.update_data(start_loop_date=date)
        await FSMClient.time_loop.set()
        await callback_query.message.edit_text(text='Оберіть час, коли вони будуть публікуватись:',
                                               reply_markup=await FullTimePicker().start_picker())


async def full_picker_handler(callback_query: types.CallbackQuery, callback_data: dict, state: FSMContext):
    from handlers.client import FSMClient
    await callback_query.answer()
    r = await FullTimePicker().process_selection(callback_query, callback_data)
    s = await state.get_state()
    fsm_data = await state.get_data()
    job_id = fsm_data.get('job_id')
    if job_id:
        job = scheduler.get_job(job_id)
    if callback_data['act'] == 'CANCEL':
        await state.update_data(date_planning=None)
        await state.update_data(start_loop_date=None)
        await plan_menu(callback_query, state)
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
                job.remove()
                scheduler.add_job(send_message_time, trigger='date', run_date=selected_date,
                                  kwargs={'data': data})
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
            await state.reset_state(with_data=False)
            logging.info(f'POST PLANNED {data}')

        elif s == 'FSMClient:time_loop':
            if job_id:
                job_data = job.kwargs.get('data')
                job_data['time_loop'] = r.time
                job_data['r'] = r
                job.modify(kwargs={'data': job_data})
            else:
                await state.update_data(time_loop=r.time)
                await state.update_data(r=r)

            await FSMClient.skip_minutes_loop.set()
            kb = InlineKeyboardMarkup(row_width=2)
            kb.add(InlineKeyboardButton(text='1-4 хв', callback_data='1-4'),
                   InlineKeyboardButton(text='5-30 хв', callback_data='5-30'),
                   back_to_plan_menu,
                   InlineKeyboardButton(text='Без затримки', callback_data='0')
                   )
            await callback_query.message.edit_text(text='На скільки хвилин затримати публікацію?', reply_markup=kb)


async def load_skip_minutes(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    fsm_data = await state.get_data()
    job_id = fsm_data.get('job_id')
    skip_minutes = call.data
    if skip_minutes in ('0', '1-4', '5-30'):
        if job_id:
            job = scheduler.get_job(job_id)
            data = job.kwargs.get('data')
            data['skip_minutes_loop'] = skip_minutes
            job.modify(kwargs={'data': data})
        else:
            await state.update_data(skip_minutes_loop=skip_minutes)
    else:
        await full_picker_handler(callback_query=call, state=state, callback_data={})
    await FSMClient.skip_days_loop.set()
    kb = InlineKeyboardMarkup()
    kb.add(back)
    await call.message.edit_text(text='Скільки днів пропускати між постами?\n\n'
                                      '<i>Якщо потрібно, щоб пост виходив кожного дня, надішліть "0"</i>',
                                 parse_mode='html', reply_markup=kb)


async def load_skip_days_add_job(message, state: FSMContext):
    if isinstance(message, types.Message):
        if message.text.isdigit():
            data = await state.get_data()
            days_skip = int(message.text)
            job_id = data.get('job_id')
            if job_id:
                job = scheduler.get_job(job_id)
                data = job.kwargs.get('data')
                data['skip_days_loop'] = days_skip
                job.modify(kwargs={'data': data})
            else:
                await state.update_data(skip_days_loop=days_skip)

            r = data.get('r')
            time_loop = data.get('time_loop')

            min_skip_minute = int(data.get('skip_minutes_loop').split('-')[0])
            add_first_minutes = timedelta(minutes=min_skip_minute)
            first_time = (r.datetime + add_first_minutes).strftime("%H:%M")

            max_skip_minute = int(data.get('skip_minutes_loop').split('-')[-1])
            add_second_minutes = timedelta(minutes=max_skip_minute)
            second_time = (r.datetime + add_second_minutes).strftime("%H:%M")

            if job_id:
                new_date: datetime = data.get('start_loop_date').replace(hour=time_loop.hour, minute=time_loop.minute)

                job.reschedule(trigger='interval', days=int(days_skip) + 1, start_date=str(new_date))
                if days_skip == 0:
                    text = f'Змінено: публікація щодня в діапазоні {first_time} - {second_time}'
                else:
                    text = f'Змінено: публікація з проміжком в {days_skip} дні(-в) в діапазоні {first_time} - {second_time}'
                await message.answer(text, reply_markup=change_create_post_kb)
                logging.info(f'POST RE-PLANNED {data}')

            else:
                data = await state.get_data()
                if days_skip == 0:
                    text = f'Пост буде публікуватись щодня в діапазоні {first_time} - {second_time}'
                else:
                    text = f'Пост буде публікуватись з проміжком в {days_skip} дні(-в) в діапазоні {first_time} - {second_time}'
                new_date: datetime = data.get('start_loop_date').replace(hour=time_loop.hour, minute=time_loop.minute)
                await message.answer(text, reply_markup=change_create_post_kb)
                add_job = scheduler.add_job(send_message_cron, trigger='interval', days=int(days_skip) + 1,
                                  start_date=str(new_date), kwargs={'data': data})
                data['job_id'] = add_job.id
                scheduler.modify_job(add_job.id, kwargs={'data': data})
                logging.info(f'POST PLANNED {data}')


        else:
            await message.answer(text='Введіть коректне значення:')

    else:
        await FSMClient.skip_minutes_loop.set()
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(InlineKeyboardButton(text='1-4 хв', callback_data='1-4'),
               InlineKeyboardButton(text='5-30 хв', callback_data='5-30'),
               back_to_plan_menu)
        await message.message.edit_text(text='На скільки хвилин затримати публікацію?', reply_markup=kb)


async def pick_time_random_v_notes(callback_query: types.CallbackQuery, callback_data: dict, state: FSMContext):
    r = await FullTimePicker().process_selection(callback_query, callback_data)
    await callback_query.answer()
    if r.status.name == 'CANCELED':
        await number_of_random_videos(callback_query, state)
        return
    if r.selected:
        data = await state.get_data()
        job_id = data.get('job_id')
        new_date = r.datetime.replace(year=datetime.now().year, month=datetime.now().month, day=datetime.now().day)
        selected_time_str = r.time.strftime("%H:%M")
        minutes_to_add = timedelta(minutes=4)
        selected_time_str_4min = (r.datetime + minutes_to_add).strftime("%H:%M")
        if job_id:
            job = scheduler.get_job(job_id)
            job_data = job.kwargs.get('data')
            days_skip = job_data.get('skip_days_loop_vnotes')
            job_data['time_random_video_notes'] = r.time
            job.reschedule(trigger='interval', days=int(days_skip) + 1, start_date=str(new_date))
            if days_skip == 0:
                text = f'Змінено: відеоповідомлення кожного дня в діапазоні {selected_time_str} - {selected_time_str_4min}'
            else:
                text = f'Змінено: відеоповідомлення з проміжком в {days_skip} дні(-в) в діапазоні {selected_time_str} - {selected_time_str_4min}'
            logging.info(f'VIDEO NOTE RE-PLANNED {job_data}')

        else:
            await state.update_data(time_random_video_notes=r.time)
            await state.update_data(post_type='looped')
            data = await state.get_data()
            days_skip = data.get('skip_days_loop_vnotes')
            if days_skip == 0:
                text = f'Відеоповідомлення будуть публікуватись кожного дня о {selected_time_str}.'
            else:
                text = f'Відеоповідомлення будуть публікуватись з проміжком в {days_skip} дні(-в) о {selected_time_str}.'
            await callback_query.message.answer(text=text, reply_markup=change_create_post_kb)
            scheduler.add_job(send_v_notes_cron, trigger='interval', days=int(days_skip) + 1, start_date=str(new_date),
                              kwargs={'data': data})
            logging.info(f'VIDEO NOTE PLANNED {data}')

        await state.reset_state(with_data=False)


def register_handlers_schedule(dp: Dispatcher):
    from handlers.client import FSMClient
    dp.register_callback_query_handler(plan_menu, Text(equals='Планування'), state='*')
    dp.register_callback_query_handler(choose_plan_date, Text(equals='Запланувати'), state='*')
    dp.register_callback_query_handler(enter_start_loop_date, Text(equals='Зациклити'), state='*')
    dp.register_callback_query_handler(load_skip_minutes, state=FSMClient.skip_minutes_loop)
    # dp.register_message_handler(choose_loop_time, state=FSMClient.skip_days_loop)

    # planning
    dp.register_callback_query_handler(process_simple_calendar, simple_cal_callback.filter(),
                                       state=FSMClient.date_planning)
    dp.register_callback_query_handler(full_picker_handler, full_timep_callback.filter(), state=FSMClient.time_planning)

    # looping
    dp.register_callback_query_handler(load_start_date_enter_time, simple_cal_callback.filter(),
                                       state=FSMClient.start_loop_date)
    dp.register_callback_query_handler(full_picker_handler, full_timep_callback.filter(), state=FSMClient.time_loop)
    dp.register_message_handler(load_skip_days_add_job, state=FSMClient.skip_days_loop)
    dp.register_callback_query_handler(load_skip_days_add_job, state=FSMClient.skip_days_loop)

    dp.register_callback_query_handler(pick_time_random_v_notes, full_timep_callback.filter(),
                                       state=FSMClient.time_random_video_notes)
