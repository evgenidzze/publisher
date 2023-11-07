from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram_timepicker.panel import FullTimePicker, full_timep_callback

from create_bot import bot, scheduler
from json_functionality import get_all_channels
from keyboards.kb_client import main_kb, add_channel_inline
from keyboards.kb_signals import signal_menu_kb, back_to_signal_menu_inline, back_to_choose_channel_inline, \
    back_to_enter_bet_inline, back_to_enter_coef_inline, back_enter_signal_count_inline

from utils import kb_channels, is_float_int, cron_signals


async def signal_menu(message, state: FSMContext):
    await state.finish()
    if isinstance(message, types.Message):
        await message.answer(text='Панель управління групами сигналів', reply_markup=signal_menu_kb)
    elif isinstance(message, types.CallbackQuery):
        await message.answer()
        try:
            await message.message.edit_text(text='Панель управління групами сигналів', reply_markup=signal_menu_kb)
        except:
            pass


async def create_signal_choose_channel(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    await state.reset_state(with_data=False)
    if get_all_channels(call.from_user.id):

        kb = await kb_channels(call, bot)
        kb.add(back_to_signal_menu_inline)
        from handlers.client import FSMClient
        await FSMClient.signal_channel_id.set()
        try:
            await call.message.edit_text(text='Оберіть канал, у якому бажаєте створити групу сигналів:',
                                         reply_markup=kb)
        except:
            pass
    else:
        add_channel_kb = InlineKeyboardMarkup().add(add_channel_inline)
        await call.message.edit_text(text='У вас немає підключених каналів.', reply_markup=add_channel_kb)


async def load_channel_enter_bet(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    await state.update_data(signal_channel_id=call.data)
    try:
        from handlers.client import FSMClient
        await FSMClient.signal_bet.set()
        kb = InlineKeyboardMarkup()
        kb.add(back_to_choose_channel_inline)
        await call.message.edit_text(text='Введіть ставку:', reply_markup=kb)
    except:
        pass


async def load_bet_enter_coef(message, state: FSMContext):
    if isinstance(message, types.Message):
        bet = message.text
        if bet.isdigit():
            kb = InlineKeyboardMarkup()
            kb.add(back_to_enter_bet_inline)
            await state.update_data(signal_bet=bet)
            await message.answer(text='Ставку збережено.\n'
                                      'Введіть через дефіс(-) діапазон коефіцієнту виграшу:\n'
                                      '<i>Наприклад</i>: <b>2 - 3.21</b>', parse_mode='html', reply_markup=kb)
            from handlers.client import FSMClient
            await FSMClient.signal_coef.set()
        else:
            kb = InlineKeyboardMarkup()
            kb.add(back_to_choose_channel_inline)
            await message.answer(text='Невірний формат, спробуйте ще раз:', reply_markup=kb)

    elif isinstance(message, types.CallbackQuery):
        try:
            kb = InlineKeyboardMarkup()
            kb.add(back_to_enter_bet_inline)
            from handlers.client import FSMClient
            await FSMClient.signal_coef.set()
            await message.message.edit_text(text='Введіть через дефіс(-) діапазон коефіцієнту виграшу:\n'
                                                 '<i>Наприклад</i>: <b>2 - 3.21</b>', parse_mode='html',
                                            reply_markup=kb)
        except:
            pass


async def load_coef_enter_count_signals(message, state: FSMContext):
    from handlers.client import FSMClient
    if isinstance(message, types.Message):
        if '-' in message.text:
            coef = message.text.split('-')
            start_coef = coef[0].strip().replace(',', '.')
            end_coef = coef[1].strip().replace(',', '.')
            if is_float_int(start_coef) and is_float_int(end_coef):  # start and end is numbers
                if float(start_coef) < float(end_coef):
                    kb = InlineKeyboardMarkup()
                    kb.add(back_to_enter_coef_inline)
                    start_coef = float(start_coef)
                    end_coef = float(end_coef)
                    await state.update_data(start_coef=start_coef)
                    await state.update_data(end_coef=end_coef)
                    await FSMClient.signals_count.set()
                    await message.answer(text=f'Діапазон коефіцієнтів ({start_coef} - {end_coef}) збережено.\n'
                                              'Введіть кількість сигналів:', reply_markup=kb)
                else:
                    kb = InlineKeyboardMarkup()
                    kb.add(back_to_enter_bet_inline)
                    await message.answer(text='Стартовий коефіцієнт має бути менший ніж кінцевий, спробуйте ще раз:',
                                         reply_markup=kb)
            else:
                kb = InlineKeyboardMarkup()
                kb.add(back_to_enter_bet_inline)
                await message.answer(text='Невірний формат, спробуйте ще раз:', reply_markup=kb)
        else:
            kb = InlineKeyboardMarkup()
            kb.add(back_to_enter_bet_inline)
            await message.answer(text='Невірний формат, введіть діапазон через дефіс:', reply_markup=kb)
    elif isinstance(message, types.CallbackQuery):
        await FSMClient.signals_count.set()
        kb = InlineKeyboardMarkup()
        kb.add(back_to_enter_coef_inline)
        try:
            await message.message.edit_text(text='Введіть кількість сигналів:', reply_markup=kb)
        except:
            pass


#
async def load_count_enter_period_time(message, state: FSMContext):
    if isinstance(message, types.Message):
        count = message.text
        if count.isdigit():
            if 1 <= int(count) <= 10:
                kb = InlineKeyboardMarkup()
                kb.add(back_enter_signal_count_inline)
                await state.update_data(signals_count=count)
                from handlers.client import FSMClient
                await FSMClient.signal_period_minutes.set()
                await message.answer(text=f'Кількість сигналів {count}.\n'
                                          f'Введіть проміжок часу між публікаціями сигналів (у хвилинах):',
                                     reply_markup=kb)

            else:
                kb = InlineKeyboardMarkup()
                kb.add(back_to_enter_coef_inline)
                await message.answer(text='Кількість сигналів має бути від 1 до 10, спробуйте ще раз:', reply_markup=kb)
        else:
            kb = InlineKeyboardMarkup()
            kb.add(back_to_enter_coef_inline)
            await message.answer(text='Невірний формат, спробуйте ще раз:', reply_markup=kb)
    elif isinstance(message, types.CallbackQuery):
        kb = InlineKeyboardMarkup()
        kb.add(back_enter_signal_count_inline)
        from handlers.client import FSMClient
        await FSMClient.signal_period_minutes.set()
        await message.message.answer(text=f'Введіть проміжок часу між публікаціями сигналів (у хвилинах):',
                                     reply_markup=kb)


async def load_period_enter_start_time(message: types.Message, state: FSMContext):
    text_data = message.text
    if text_data.isdigit():
        from handlers.client import FSMClient
        await FSMClient.start_time.set()
        await state.update_data(signal_period_minutes=text_data)
        await message.answer(text="Сигнали будуть виходити кожного дня в обраний час: ",
                             reply_markup=await FullTimePicker().start_picker())
    else:
        kb = InlineKeyboardMarkup()
        kb.add(back_enter_signal_count_inline)
        await message.answer(text="Невірний формат, введіть число:", reply_markup=kb)


async def load_start_time(callback_query: types.CallbackQuery, callback_data: dict, state: FSMContext):
    await callback_query.answer()
    r = await FullTimePicker().process_selection(callback_query, callback_data)
    if r.status.name == 'CANCELED':
        await load_count_enter_period_time(callback_query, state)
    elif r.selected:
        await state.update_data(start_time=r.time)
        data = await state.get_data()
        scheduler.add_job(cron_signals, trigger='cron', hour=r.time.hour, minute=r.time.minute,
                          kwargs={'data': data})
        selected_time_str = r.time.strftime("%H:%M")
        await callback_query.message.answer(text=f'Розсилка сигналів буде починатись кожного дня о {selected_time_str}',
                                            reply_markup=main_kb)
        await state.finish()


async def delete_signal_choose_channel(call: types.CallbackQuery, state: FSMContext):
    from handlers.client import FSMClient
    await call.answer()
    await state.reset_state(with_data=False)
    if get_all_channels(call.from_user.id):
        kb = await kb_channels(call, bot)
        kb.add(back_to_signal_menu_inline)
        await FSMClient.del_signal_channel_id.set()
        try:
            await call.message.edit_text(text='Оберіть канал, в якому бажаєте видалити групу сигналів:',
                                         reply_markup=kb)
        except:
            pass
    else:
        add_channel_kb = InlineKeyboardMarkup().add(add_channel_inline)
        await call.message.edit_text(text='У вас немає підключених каналів.', reply_markup=add_channel_kb)


async def channel_signals_list_delete(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    channel_id = call.data
    all_jobs = scheduler.get_jobs()
    channel_signals = {}
    if all_jobs:
        for job in all_jobs:
            job_data = job.kwargs.get('data')
            if channel_id in job_data['signal_channel_id']:
                channel_signals[job.id] = job_data
        if channel_signals:
            kb = InlineKeyboardMarkup()
            from handlers.client import FSMClient
            await FSMClient.del_signal_id.set()
            for signal in channel_signals:
                signal_time = channel_signals[signal]['start_time'].strftime("%H:%M")
                start_coef = channel_signals[signal]['start_coef']
                end_coef = channel_signals[signal]['end_coef']
                signals_count = channel_signals[signal]['signals_count']
                kb.add(
                    InlineKeyboardButton(text=f"{signal_time} - коеф.({start_coef}-{end_coef}), к-сть:{signals_count}",
                                         callback_data=job.id))
            kb.add(back_to_signal_menu_inline)
            await call.message.answer(text='Оберіть сигнал, який бажаєте видалити.', reply_markup=kb)

        else:
            await call.message.answer(text='У каналі не встановлені сигнали.', reply_markup=signal_menu_kb)

    else:
        await call.message.answer(text='У каналі не встановлені сигнали.', reply_markup=signal_menu_kb)


async def delete_signal(call: types.CallbackQuery):
    try:
        scheduler.remove_job(call.data)
        await call.message.answer(text='✅ Сигнал видалено з каналу.', reply_markup=signal_menu_kb)
    except:
        pass


async def my_signals(call: types.CallbackQuery):
    await call.answer()
    all_jobs = scheduler.get_jobs()
    signal_jobs = {}
    if all_jobs:
        for job in all_jobs:
            if 'signal_channel_id' in job.kwargs.get('data'):
                signal_channel_id = job.kwargs.get('data')['signal_channel_id']
                if not signal_channel_id in signal_jobs:
                    signal_jobs[signal_channel_id] = []
                signal_jobs[signal_channel_id].append(job.kwargs.get('data'))

        if signal_jobs:
            try:
                result = ''
                for job in signal_jobs:
                    channel = await bot.get_chat(job)
                    channel_name = channel.title
                    result += f'{channel_name}:\n'
                    for signal in signal_jobs.get(job):
                        result += f'\t-Кожного дня о {signal.get("start_time").strftime("%H:%M")}; Діапазон: {signal.get("start_coef")}-{signal.get("end_coef")}\n'

                await call.message.edit_text(text=result, reply_markup=signal_menu_kb)
            except:
                pass

        else:
            try:
                await call.message.edit_text(text='Немає встановлених сигналів', reply_markup=signal_menu_kb)
            except:
                pass
    else:
        try:
            await call.message.edit_text(text='Немає встановлених сигналів', reply_markup=signal_menu_kb)
        except:
            pass


def register_handlers_client(dp: Dispatcher):
    from handlers.client import FSMClient
    dp.register_callback_query_handler(create_signal_choose_channel, Text(equals='create_signal_group'), state='*')
    dp.register_callback_query_handler(delete_signal_choose_channel, Text(equals='delete_signal_group'), state='*')
    dp.register_callback_query_handler(my_signals, Text(equals='my_signal_groups'), state='*')
    dp.register_callback_query_handler(load_channel_enter_bet, state=FSMClient.signal_channel_id)
    dp.register_callback_query_handler(load_channel_enter_bet, Text(equals='enter_bet'), state='*')

    dp.register_message_handler(load_bet_enter_coef, state=FSMClient.signal_bet)
    dp.register_callback_query_handler(load_bet_enter_coef, Text(equals='enter_coef'), state='*')

    dp.register_message_handler(load_coef_enter_count_signals, state=FSMClient.signal_coef)
    dp.register_callback_query_handler(load_coef_enter_count_signals, Text(equals='enter_signal_count'), state='*')
    #
    dp.register_message_handler(load_count_enter_period_time, state=FSMClient.signals_count)
    dp.register_callback_query_handler(load_count_enter_period_time, Text(equals='enter_period_time'), state='*')

    dp.register_message_handler(load_period_enter_start_time, state=FSMClient.signal_period_minutes)
    dp.register_callback_query_handler(load_start_time, full_timep_callback.filter(), state=FSMClient.start_time)

    dp.register_callback_query_handler(channel_signals_list_delete, state=FSMClient.del_signal_channel_id)
    dp.register_callback_query_handler(delete_signal, state=FSMClient.del_signal_id)
