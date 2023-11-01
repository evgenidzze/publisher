import datetime
import io
import locale
from copy import deepcopy
from typing import List
import aiogram.utils.exceptions
import aiohttp
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram_calendar import SimpleCalendar

from aiogram_media_group import media_group_handler
from config import TOKEN_API
from create_bot import bot, scheduler
from handlers.catalog_handlers import media_type_from_cat, media_base_panel

from handlers.signals import signal_menu

from utils import kb_channels, AuthMiddleware, send_voice_from_audio, restrict_media, set_caption, send_post, \
    pressed_back_button, add_random_media, send_v_notes_cron, sorting_key_jobs, show_post, job_list_by_channel
from json_functionality import get_all_channels, save_channel_json, remove_channel_id_from_json, catalog_list_json, \
    get_catalog, get_video_notes_by_cat

from keyboards.kb_client import main_kb, kb_manage_channel_inline, cancel_kb, post_formatting_kb, add_channel_inline, \
    create_post_inline_kb, back_kb, base_manage_panel_kb, no_text_kb, del_voice_kb, add_posts_to_kb, take_from_db, \
    media_kb, inlines_menu_kb, back, self_or_random_kb, del_post_inline, back_to_main_menu, back_edit_post_inline, \
    change_create_post_kb, create_post_inline, back_to_my_posts_inline, back_to_media_settings, my_posts_inline, \
    random_v_note_kb
from aiogram_calendar import simple_cal_callback
from aiogram_timepicker.panel import FullTimePicker, full_timep_callback

locale.setlocale(locale.LC_ALL, 'uk_UA.utf8')


class FSMClient(StatesGroup):
    inline_to_delete = State()
    new_cat_name = State()
    time_random_video_notes = State()
    # random_v_notes_id = State()
    posts_by_data = State()
    all_posts_channel_id = State()
    del_signal_id = State()
    del_signal_channel_id = State()
    start_time = State()
    signal_period_minutes = State()
    signals_count = State()
    signal_coef = State()
    signal_bet = State()
    signal_channel_id = State()
    inline_link = State()
    inline_text = State()
    channel_change_post = State()
    random_or_self = State()
    number_of_rand_video = State()
    number_of_rand_photo = State()
    choose_catalog = State()
    user_name = State()
    post_text = State()
    remove_channel_id = State()
    channel_id = State()
    create_post_in_channel = State()
    date_planning = State()
    time_planning = State()
    time_loop = State()
    media_answer = State()

    create_cat_name = State()
    show_catalog = State()  # show catalog content
    edit_catalog = State()  # choose add or remove media
    add_delete_cat_media = State()  # if delete - pick a type if add - load media
    catalog_media_type_remove = State()  # request media number
    del_cat_media_number = State()  # receive num of media and remove
    loaded_catalog_file = State()
    catalog_for_post = State()
    del_catalog = State()
    media_type_add_from_cat = State()
    add_media_from_cat = State()

    loaded_post_files = State()
    voice = State()
    job_id = State()
    job_modify = State()
    del_voice_or_vnote_answer = State()
    del_media_answer = State()


async def start_command(message: Message, state: FSMContext):
    await state.finish()
    if message.chat.type != types.ChatType.GROUP:
        await message.answer(text=f'Вітаю, {message.from_user.username}\n'
                                  f'Це бот для відкладеного постингу. Для початку роботи '
                                  f'скористайтеся командами або головним меню.\n'
                                  f'/addchannel – підключення нового каналу',
                             reply_markup=main_kb)


async def main_menu(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await call.answer()
    await call.message.answer(text='Головне меню ⬇️', reply_markup=main_kb)


async def channel_manage_menu(message: types.Message, state: FSMContext):
    await state.finish()
    await bot.send_message(chat_id=message.from_user.id, text="Панель управління каналами",
                           reply_markup=kb_manage_channel_inline)


async def deny_channel(message: types.Message):
    await FSMClient.remove_channel_id.set()
    all_channels = get_all_channels(message.from_user.id)
    channel_list = '\n'.join([f"{name} <code>{key}</code>" for key, name in all_channels.items()])

    await bot.send_message(chat_id=message.from_user.id,
                           text=f'Надішліть id каналу, який хочете відключити.\n\n'
                                f'{channel_list}', reply_markup=cancel_kb, parse_mode="html")


async def remove_channel_id(message: types.Message, state: FSMContext):
    channel_id = str(message.text)
    if channel_id[1:].isdigit():
        await remove_channel_id_from_json(channel_id, message)
        await state.finish()
    else:
        await message.answer('id має складатись тільки з цифр, надішліть ще раз.')


async def add_channel(message, state: FSMContext):
    await state.finish()
    await FSMClient.channel_id.set()
    me = await bot.me
    bot_name = me.username

    if isinstance(message, types.CallbackQuery):
        await message.answer()
        await message.message.answer(
            text="Щоб підключити канал, призначте бота його адміністратором. Для цього:\n1. Перейдіть в канал.\n2. "
                 "Натисніть на назву каналу, щоб відкрити його налаштування.\n3. Перейдіть в «Адміністратори» → «Додати "
                 f"адміністратора».\n4. Введіть в пошуку <code>@{bot_name}</code>. У результатах пошуку побачите вашого бота. "
                 "Клікніть по ньому, потім натисніть «Готово».\nПісля цього перешліть сюди будь-яке повідомлення з каналу.",
            parse_mode='html', reply_markup=cancel_kb)
    else:
        await message.answer(
            text="Щоб підключити канал, призначте бота його адміністратором. Для цього:\n1. Перейдіть в канал.\n2. "
                 "Натисніть на назву каналу, щоб відкрити його налаштування.\n3. Перейдіть в «Адміністратори» → «Додати "
                 f"адміністратора».\n4. Введіть в пошуку <code>@{bot_name}</code>. У результатах пошуку побачите вашого бота. "
                 "Клікніть по ньому, потім натисніть «Готово».\nПісля цього перешліть сюди будь-яке повідомлення з каналу.",
            parse_mode='html', reply_markup=cancel_kb)


async def load_channel_id(message: types.Message, state: FSMContext):
    if 'forward_from_chat' in message:
        channel_chat_id = str(message.forward_from_chat.id)
        me = await bot.get_me()
        bot_id = me.id
        bot_name = me.username
        chat_member = await bot.get_chat_member(chat_id=channel_chat_id, user_id=bot_id)
        bot_status = chat_member.status
        if bot_status == 'administrator':
            await save_channel_json(channel_id=channel_chat_id, message=message)
            await state.finish()
        else:
            await state.finish()
            await message.answer(
                text=f'⛔️ Немає доступу. Переконайтеся, що бот <code>@{bot_name}</code> доданий до адміністраторів каналу '
                     f'<a href="{await message.forward_from_chat.get_url()}">{message.forward_from_chat.title}</a>.',
                parse_mode='html')
    else:
        await message.answer(text='Потрібно переслати повідовлення саме з каналу.\n'
                                  'Спробуйте ще раз.')


async def channel_list(call: types.CallbackQuery):
    await call.answer()
    all_channels = get_all_channels(call.from_user.id)

    try:
        if all_channels:
            channel_list = '\n'.join([f"{name} <code>{key}</code>" for key, name in all_channels.items()])

            await call.message.edit_text(text=channel_list, parse_mode='html',
                                         reply_markup=kb_manage_channel_inline)
        else:
            add_channel_kb = InlineKeyboardMarkup().add(add_channel_inline)
            await call.message.edit_text(text='У вас немає каналів', reply_markup=add_channel_kb)
    except:
        pass


async def edit_create_post_channel_list(message, state: FSMContext):
    jobs = scheduler.get_jobs()
    if jobs:
        for job in jobs:
            print(job.kwargs.get('data'))

    if isinstance(message, types.Message):
        await state.finish()
        if get_all_channels(message.from_user.id):
            kb = await kb_channels(message, bot)
            kb.add(back_to_main_menu)
            if message.text == 'Створити пост':
                await FSMClient.create_post_in_channel.set()
                await message.answer(text='Оберіть канал, у якому хочете створити пост:', reply_markup=kb,
                                     parse_mode='html')
            else:
                await FSMClient.channel_change_post.set()
                await message.answer(text='Оберіть канал, у якому хочете змінити пост:', reply_markup=kb,
                                     parse_mode='html')
        else:
            await add_channel(message, state)
    elif isinstance(message, types.CallbackQuery):
        await message.answer()
        if get_all_channels(message.from_user.id):
            kb = await kb_channels(message, bot)
            if message.data == 'Створити пост':
                await state.finish()
                await FSMClient.create_post_in_channel.set()
                await message.message.answer(text='Оберіть канал, у якому хочете створити пост:', reply_markup=kb,
                                             parse_mode='html')
            elif message.data in ('Змінити пост', 'back'):
                await FSMClient.channel_change_post.set()
                try:
                    await message.message.edit_text(text='Оберіть канал, у якому хочете змінити пост:', reply_markup=kb,
                                                    parse_mode='html')
                except:
                    pass
            else:
                try:
                    kb = InlineKeyboardMarkup()
                    kb.add(create_post_inline, my_posts_inline)
                    await message.message.answer(text='Бажаєте створити новий пост або оглянути існуючі?',
                                                 reply_markup=kb)
                except:
                    pass
        else:
            await add_channel(message.message, state)


async def edit_post_list(message: types.CallbackQuery, state: FSMContext):
    # await state.finish()
    channel_id = message.data
    jobs = scheduler.get_jobs()
    edit_kb = InlineKeyboardMarkup()
    posts = []
    jobs = sorted(jobs, key=lambda job: job.next_run_time)
    for job in jobs:
        job_data = job.kwargs.get('data')
        if job_data.get('channel_id') == channel_id:
            posts.append(job)
    if posts:
        add_posts_to_kb(jobs=posts, edit_kb=edit_kb)
        edit_kb.add(back_edit_post_inline)
        await message.answer()
        await message.message.answer('Ваші заплановані та зациклені пости.\n'
                                     'Оберіть потрібний вам:', reply_markup=edit_kb)
        await FSMClient.job_id.set()
    else:
        await message.answer()
        try:
            await message.message.edit_text('У вас немає запланованих або зациклених постів.',
                                            reply_markup=create_post_inline_kb)
        except:
            pass


async def change_job(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    job_id = call.data
    job = scheduler.get_job(job_id=job_id)
    await state.update_data(job_id=job_id)

    job_data = job.kwargs.get('data')
    # post_text = job_data.get("post_text")
    # post_media_files = job_data.get('loaded_post_files')
    # post_voice = job_data.get('voice')
    # post_video_note = job_data.get('video_note')
    #
    # link_kb = job_data.get('inline_kb')
    await show_post(call, state)

    await state.reset_state(with_data=False)

    if job_id:
        kb_job = deepcopy(post_formatting_kb)
        del kb_job.inline_keyboard[-1]
        kb_job.add(del_post_inline)
        await call.message.answer(
            text='Налаштуйте оформлення посту', reply_markup=kb_job)
    else:
        await call.message.answer(
            text='Налаштуйте оформлення посту', reply_markup=post_formatting_kb)


async def enter_change_text(message: types.CallbackQuery, state: FSMContext):
    fsm_data = await state.get_data()
    job_id = fsm_data.get('job_id')
    if fsm_data.get('channel_id'):
        channel_id = fsm_data.get('channel_id')
    elif job_id:
        job_data = scheduler.get_job(job_id).kwargs.get('data')
        channel_id = job_data['channel_id']
    else:
        channel_id = message.data

    channel = await bot.get_chat(channel_id)
    channel_name = channel.title
    await state.update_data(channel_id=channel_id)

    await FSMClient.post_text.set()
    try:
        await message.message.edit_text(
            text=f'Надішліть текст посту, який хочете опублікувати в каналі\n«{channel_name}».',
            reply_markup=no_text_kb)
    except:
        pass
    await message.answer()


async def load_changed_text(message, state: FSMContext):
    text = None
    if isinstance(message, types.Message):
        text = message.text
    else:
        await message.answer()
    data = await state.get_data()
    job_id = data.get('job_id')
    if job_id:
        job = scheduler.get_job(job_id)
        data = job.kwargs.get('data')
        data['post_text'] = text
        job.modify(kwargs={'data': data})
    else:
        await state.update_data(post_text=text)
    await show_post(message, state)

    await bot.send_message(chat_id=message.from_user.id, text='Налаштуйте оформлення посту.',
                           reply_markup=post_formatting_kb)
    await state.reset_state(with_data=False)


async def formatting_main_menu(message, state: FSMContext):
    data = await state.get_data()
    job_id = data.get('job_id')
    if job_id:
        job = scheduler.get_job(job_id)
        data = job.kwargs.get('data')

    if isinstance(message, types.CallbackQuery):
        await message.answer()
        if message.data in ('back', 'formatting_main_menu', 'full_timepicker:CANCEL:-1:-1:-1'):
            await state.update_data(date_planning=None)
            if message.message.text == 'У вас немає запланованих або зациклених постів.':
                await edit_create_post_channel_list(message, state)
                return
            else:
                try:
                    await message.message.edit_text(text='Налаштуйте оформлення посту.',
                                                    reply_markup=post_formatting_kb)
                except:
                    await message.message.answer(text='Налаштуйте оформлення посту.',
                                                 reply_markup=post_formatting_kb)
    else:
        await message.answer(text='Налаштуйте оформлення посту.',
                             reply_markup=post_formatting_kb)
    await state.reset_state(with_data=False)


async def make_post_now(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    data = await state.get_data()
    job_id = data.get('job_id')
    if job_id:
        data = scheduler.get_job(job_id).kwargs['data']
    keys_to_check = ['post_text', 'loaded_post_files', 'voice', 'video_note', 'random_photos_number',
                     'random_videos_number']
    if any(data.get(key) for key in keys_to_check):
        channel_id = data.get('channel_id')
        chat_info = await bot.get_chat(chat_id=channel_id)
        chat_title = chat_info.title
        chat_url = await chat_info.get_url()
        post_text = data.get("post_text")
        post_media_files = data.get('loaded_post_files')
        post_voice = data.get('voice')
        post_video_note = data.get('video_note')
        inline_kb = data.get('inline_kb')
        cat_name = data.get('choose_catalog')

        if post_text is None:
            post_text = ''

        if not post_media_files and (data.get('random_photos_number') or data.get('random_videos_number')):
            post_media_files = types.MediaGroup()
            add_random_media(media_files=post_media_files, data=data, cat_name=cat_name)
        await send_post(post_media_files=post_media_files, post_text=post_text, post_voice=post_voice,
                        channel_id=channel_id, post_video_note=post_video_note, bot=bot, inline_kb=inline_kb)

        await call.message.delete()
        await call.message.answer(
            text=f'🚀 Повідомлення {post_text} опубліковано у <a href="{chat_url}">{chat_title}</a>.',
            reply_markup=main_kb, parse_mode='html')
        await state.finish()
    else:
        await call.message.answer(text='❌ Ви не можете опублікувати пост, так як у ньому немає контенту.\n'
                                       'Наповніть пост текстом або медіа:',
                                  reply_markup=post_formatting_kb)


async def choose_or_self_media(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    await FSMClient.media_answer.set()
    media_choice_custom_kb = InlineKeyboardMarkup(row_width=2)
    media_choice_custom_kb.add(take_from_db)
    try:
        await call.message.edit_text(text='Оберіть варіант:', reply_markup=media_kb)
    except:
        pass


async def load_media_answer(call: types.CallbackQuery, state: FSMContext):
    await call.answer()

    data = call.data
    fsm_data = await state.get_data()
    if data == 'formatting_main_menu':
        await formatting_main_menu(call, state)
    #
    # elif data == 'Запланувати':
    #     await state.reset_state(with_data=False)
    #     await nav_cal_handler(call, state)
    #
    # elif data == 'Зациклити':
    #     await state.reset_state(with_data=False)
    #     await post_looping(call, state)
    #
    # elif data == 'post_now_menu':
    #     await state.reset_state(with_data=False)
    #     await post_now_menu_handler(call, state)

    elif data in 'take_from_db':
        catalogs = catalog_list_json()
        catalogs_kb = InlineKeyboardMarkup()
        if catalogs:
            for cat in catalogs:
                catalogs_kb.add(InlineKeyboardButton(text=cat, callback_data=cat))
            catalogs_kb.add(back)
            await FSMClient.choose_catalog.set()
            try:
                await call.message.edit_text(text='Оберіть каталог', reply_markup=catalogs_kb)
            except:
                pass
        else:
            await state.reset_state(with_data=False)
            kb = deepcopy(base_manage_panel_kb)
            kb.add(back_to_media_settings)
            try:
                await call.message.edit_text(text='Немає жодного каталогу', reply_markup=kb)
            except:
                pass

    elif data == 'send_by_self':
        await FSMClient.loaded_post_files.set()
        await call.message.edit_text(text='🎞 Надішліть або перешліть сюди медіа.\n'
                                          'Можете також надіслати згруповані фото або відео:\n'
                                          '\t<i>-фото;</i>\n'
                                          '\t<i>-відео;</i>\n'
                                          '\t<i>-голосове повідомлення;</i>\n'
                                          '\t<i>-файл;</i>', parse_mode='html', reply_markup=back_kb)

    elif data == 'remove_media':
        if not fsm_data.get('job_id'):
            if any(fsm_data.get(key) for key in ('voice', 'loaded_post_files', 'video_note')):
                voice = fsm_data.get('voice')
                loaded_post_files = fsm_data.get('loaded_post_files')
                video_note = fsm_data.get('video_note')
                if voice:
                    await FSMClient.del_voice_or_vnote_answer.set()
                    await call.message.answer_voice(voice=voice)
                    await call.message.answer(text='Бажаєте видалити голосове з посту?', reply_markup=del_voice_kb)
                elif video_note:
                    await FSMClient.del_voice_or_vnote_answer.set()
                    await call.message.answer_video_note(video_note=video_note)
                    await call.message.answer(text='Бажаєте видалити відеоповідомлення з посту?',
                                              reply_markup=del_voice_kb)
                elif loaded_post_files:
                    media: types.MediaGroup = fsm_data.get('loaded_post_files')
                    for m in range(len(media.media)):
                        if media.media[m].type == 'video':
                            await call.message.answer_video(video=media.media[m].media, caption=m + 1)
                        elif media.media[m].type == 'photo':
                            await call.message.answer_photo(photo=media.media[m].media, caption=m + 1)
                        elif media.media[m].type == 'document':
                            await call.message.answer_document(document=media.media[m].media, caption=m + 1)
                    await FSMClient.del_media_answer.set()
                    await call.message.answer(text='Надішліть номер медіа, яке хочете прибрати з посту:',
                                              reply_markup=back_kb)

            else:
                try:
                    await call.message.edit_text(text="У пості немає медіа.", reply_markup=media_kb)
                except:
                    pass

        elif fsm_data.get('job_id'):
            job = scheduler.get_job(fsm_data.get('job_id'))
            job_data = job.kwargs.get('data')

            if any(job_data.get(key) for key in ('voice', 'loaded_post_files')):
                voice = job_data.get('voice')
                loaded_post_files = job_data.get('loaded_post_files')
                if voice:
                    await FSMClient.del_voice_or_vnote_answer.set()
                    await call.message.answer_voice(voice=voice)
                    await call.message.answer(text='Бажаєте видалити голосове з посту?', reply_markup=del_voice_kb)
                if loaded_post_files:
                    media: types.MediaGroup = job_data.get('loaded_post_files')
                    for m in range(len(media.media)):
                        if media.media[m].type == 'video':
                            await call.message.answer_video(video=media.media[m].media, caption=m + 1)
                        elif media.media[m].type == 'photo':
                            await call.message.answer_photo(photo=media.media[m].media, caption=m + 1)
                        elif media.media[m].type == 'document':
                            await call.message.answer_document(document=media.media[m].media, caption=m + 1)
                    await FSMClient.del_media_answer.set()
                    await call.message.answer(text='Надішліть номер медіа, яке хочете прибрати з посту:')
            else:
                await state.reset_state(with_data=False)
                try:
                    await call.message.edit_text(text="У пості немає медіа.", reply_markup=post_formatting_kb)
                except:
                    pass


async def del_media(message: types.Message, state: FSMContext):
    fsm_data = await state.get_data()
    inline_kb = fsm_data.get('inline_kb')
    if isinstance(message, types.CallbackQuery):
        if message.data == 'back':
            await state.reset_state(with_data=False)
            try:
                await message.message.edit_text(text='Обрати медіа з бази чи додати самостійно?',
                                                reply_markup=media_kb)
            except:
                pass

    elif isinstance(message, types.Message):
        job_id = fsm_data.get('job_id')
        job = None
        if job_id:
            job = scheduler.get_job(job_id)
            job_data = job.kwargs.get('data')
            post_text = job_data.get('post_text')
            media: types.MediaGroup = job_data.get('loaded_post_files')

        else:
            post_text = fsm_data.get('post_text')
            media: types.MediaGroup = fsm_data.get('loaded_post_files')

        if not post_text:
            post_text = ''
        try:
            del media.media[int(message.text) - 1]
        except:
            await message.answer(text='❌ Невірний формат.\n'
                                      'Введіть 1 номер.')
        if len(media.media) > 0:
            set_caption(text=post_text, media=media),
            if job:
                job_data['loaded_post_files'] = media
                job.modify(kwargs={'data': job_data})
            else:
                await state.update_data(loaded_post_files=media)
            if len(media.media) == 1 and inline_kb:
                m = media.media[0]
                if m.type == 'video':
                    await message.answer_video(video=m.media, caption=post_text, reply_markup=inline_kb)
                elif m.type == 'photo':
                    await message.answer_photo(photo=m.media, caption=post_text, reply_markup=inline_kb)
                elif m.type == 'document':
                    await message.answer_document(document=m.media, caption=post_text, reply_markup=inline_kb)
            else:
                await message.answer_media_group(media=media)
        else:
            if job:
                del job_data['loaded_post_files']
                job.modify(kwargs={'data': job_data})
            else:
                await state.update_data(loaded_post_files=None)

        await message.answer(text=f'Медіа №{message.text} видалено з посту.\n'
                                  f'Налаштуйте оформлення посту.', reply_markup=media_kb)
        await state.reset_state(with_data=False)
        await FSMClient.media_answer.set()


async def del_voice_or_video_note(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    fsm_data = await state.get_data()
    job_id = fsm_data.get('job_id')
    if call.data == 'yes':
        if job_id:
            job = scheduler.get_job(job_id)
            job_data = job.kwargs.get('data')
            if 'voice' in job_data:
                job_data['voice'] = None
                await call.message.answer(text='✅ Голосове видалено.', reply_markup=post_formatting_kb)
            elif 'video_note' in job_data:
                job_data['video_note'] = None
                await call.message.answer(text='✅ Відео-повідомлення видалено.', reply_markup=post_formatting_kb)
            job.modify(kwargs={'data': job_data})
        else:
            if 'voice' in fsm_data:
                await state.update_data(voice=None)
                await call.message.answer(text='✅ Голосове видалено.', reply_markup=post_formatting_kb)
            elif 'video_note' in fsm_data:
                await state.update_data(video_note=None)
                await call.message.answer(text='✅ Відео-повідомлення видалено.', reply_markup=post_formatting_kb)
    elif call.data == 'no':
        try:
            await call.message.edit_text(
                text='Налаштуйте оформлення посту.',
                reply_markup=post_formatting_kb)
        except:
            pass

    else:
        return
    await state.reset_state(with_data=False)


async def del_post(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    fsm_data = await state.get_data()
    job_id = fsm_data.get('job_id')
    scheduler.remove_job(job_id)
    await call.message.answer(text='✅ Пост видалено', reply_markup=main_kb)
    await edit_create_post_channel_list(message=call, state=state)


@media_group_handler
async def load_media_file(messages: List[types.Message], state: FSMContext):
    if pressed_back_button(messages[0]):
        await state.reset_state(with_data=False)
        await choose_or_self_media(call=messages[0], state=state)
        return

    data = await state.get_data()
    job_id = data.get('job_id')

    # if job_id до дані будуть з джоба
    if job_id:
        job = scheduler.get_job(job_id)
        data = scheduler.get_job(job_id).kwargs.get('data')
    inline_kb = data.get('inline_kb')

    if data.get('random_photos_number'):
        await messages[0].answer(text='⚠️ Рандом-медіа налаштування скинуті.')
        if job_id:
            data['random_photos_number'] = None
            job.modify(kwargs={'data': data})
        else:
            await state.update_data(random_photos_number=None)

    text = data.get('post_text')
    media: types.MediaGroup = data.get('loaded_post_files')

    # якщо медіа раніше не створена то створюємо нову
    if not media:
        media = types.MediaGroup()

    if await restrict_media(messages=messages, state=state, data=data, post_formatting_kb=post_formatting_kb):
        return

    # прохід по списку меседжів у групі
    for message_num in range(len(messages)):
        if messages[message_num].content_type in ('audio', 'voice', 'video_note'):
            if 'audio' in messages[0]:
                voice_message = await send_voice_from_audio(message=messages[0], bot=bot)
                if job_id:
                    data['voice'] = voice_message.voice.file_id
                    job.modify(kwargs={'data': data})
                else:
                    await state.update_data(voice=voice_message.voice.file_id)
            elif 'voice' in messages[0]:
                await messages[0].answer_voice(messages[0].voice.file_id, caption=text)
                if job_id:
                    data['voice'] = messages[0].voice.file_id
                    job.modify(kwargs={'data': data})
                else:
                    await state.update_data(voice=messages[0].voice.file_id)
            elif 'video_note' in messages[0]:
                await messages[0].answer_video_note(messages[0].video_note.file_id)
                if job_id:
                    data['video_note'] = messages[0].video_note.file_id
                    job.modify(kwargs={'data': data})
                else:
                    await state.update_data(video_note=messages[0].video_note.file_id)

            await state.reset_state(with_data=False)
            break
        if 'video' in messages[message_num]:
            media.attach_video(video=messages[message_num].video.file_id)
        elif 'photo' in messages[message_num]:
            media.attach_photo(photo=messages[message_num].photo[0].file_id)
        elif 'document' in messages[message_num]:
            media.attach_document(messages[message_num].document.file_id)

    if media.media:
        set_caption(media=media, text=text)

        try:
            if len(media.media) == 1 and inline_kb:
                m = media.media[0]
                if m.type == 'video':
                    await messages[0].answer_video(video=m.media, caption=text, reply_markup=inline_kb)
                elif m.type == 'photo':
                    await messages[0].answer_photo(photo=m.media, caption=text, reply_markup=inline_kb)
                elif m.type == 'document':
                    await messages[0].answer_document(document=m.media, caption=text, reply_markup=inline_kb)
            else:
                await messages[0].answer_media_group(media=media)
        except aiogram.utils.exceptions.BadRequest:
            await messages[0].answer(text='❌ Цей тип медіа не може бути згрупований з попередніми медіа.')
            media.media.pop()

        if job_id:
            data['loaded_post_files'] = media
            job.modify(kwargs={'data': data})
        else:
            await state.update_data(loaded_post_files=media)

    await messages[0].answer(text='Оформіть пост або оберіть варіант публікації.',
                             reply_markup=post_formatting_kb)

    await state.reset_state(with_data=False)


async def random_or_self(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    fsm_data = await state.get_data()
    cat_name = fsm_data.get('choose_catalog')
    cat_data = get_catalog(cat_name)
    message_data = call.data
    media_len = 0
    existing_random_v_notes_id: list = fsm_data.get('random_v_notes_id')

    if message_data == 'back':
        catalogs = catalog_list_json()
        catalogs_kb = InlineKeyboardMarkup()
        if catalogs:
            for cat in catalogs:
                catalogs_kb.add(InlineKeyboardButton(text=cat, callback_data=cat))
            catalogs_kb.add(back)
            await FSMClient.choose_catalog.set()
        try:
            await call.message.edit_text(text='Оберіть каталог:', reply_markup=catalogs_kb)
        except:
            pass

    if cat_data.get('photos'):
        media_len += len(cat_data.get('photos'))
    if cat_data.get('videos'):
        media_len += len(cat_data.get('videos'))

    if message_data == 'random_media':
        if cat_data.get('photos') and media_len > 1:
            await FSMClient.number_of_rand_photo.set()
            await call.message.edit_text(
                text=f'Скільки фото буде у вибірці? (доступно {len(cat_data.get("photos"))})',
                reply_markup=back_kb)
        elif cat_data.get('videos') and media_len > 1:
            await FSMClient.number_of_rand_video.set()
            await call.message.edit_text(
                text=f'Скільки відео буде у вибірці? (доступно {len(cat_data.get("videos"))})',
                reply_markup=back_kb)
        else:
            try:
                await call.message.edit_text(text=f'<b>У каталозі має бути мінімум 2 фото або відео.</b>',
                                             parse_mode='html', reply_markup=self_or_random_kb)
            except:
                pass


    elif message_data == 'self_media':
        await media_type_from_cat(call, state)

    elif message_data == 'random_videonote':
        video_notes = get_video_notes_by_cat(cat_name)
        if video_notes:
            await state.update_data(random_v_notes_id=video_notes)
            # await FSMClient.random_v_notes_id.set()
            # for note_num in range(len(video_notes)):
            #     msg = await call.message.answer_video_note(video_note=video_notes[note_num])
            #     await msg.reply(text=str(note_num + 1))
            # if len(existing_random_v_notes_id) <= 1:
            #     await call.message.edit_text(text='У вибірці має бути мінімум 2 відеоповідомлення.\n'
            #                                       'Надішліть ще номер(-и) відеоповідомлень:',
            #                                  reply_markup=random_v_note_kb)
            # else:
            await FSMClient.time_random_video_notes.set()
            await call.message.edit_text(text='Оберіть час, коли вони будуть публікуватись:',
                                         reply_markup=await FullTimePicker().start_picker())
            # await call.message.answer(
            #     text='Введіть номер відеоповідомлення (або кілька номерів через пробіл), яке бажаєте додати.',
            #     reply_markup=back_kb)
        else:
            await call.message.edit_text(text='У каталозі має бути мінімум 2 відеоповідомлення.',
                                         reply_markup=self_or_random_kb)


# async def load_random_v_notes_id(message, state: FSMContext):
#     fsm_data = await state.get_data()
#     cat_name = fsm_data.get('choose_catalog')
#     video_notes = get_video_notes_by_cat(cat_name)
#     existing_random_v_notes_id: list = fsm_data.get('random_v_notes_id')
#
#     if isinstance(message, Message):
#         new_v_note_numbers = [num for num in message.text.split() if num.isdigit()]
#         new_v_note_id = [video_notes[int(v_id) - 1] for v_id in new_v_note_numbers if int(v_id) <= len(video_notes)]
#         if existing_random_v_notes_id:
#             existing_random_v_notes_id.extend(new_v_note_id)
#         else:
#             existing_random_v_notes_id = new_v_note_id
#         existing_random_v_notes_id = list(dict.fromkeys(existing_random_v_notes_id))
#         await state.update_data(random_v_notes_id=existing_random_v_notes_id)
#         await message.answer(
#             text=f'✅ Відеоповідомлення №{", ".join([str(num + 1) for num in range(len(existing_random_v_notes_id))])} додано.\n'
#                  f'Надішліть ще номер(-и) або натисніть кнопку "💾 Зберегти", щоб закінчити',
#             reply_markup=random_v_note_kb)
#         # else:
#         #     await message.answer(text='Введіть коректний номер:')
#     elif isinstance(message, types.CallbackQuery):
#         if message.data in ('back_to_media_variant', 'back'):
#             await state.update_data(random_v_notes_id=None)
#             await number_of_random_videos(message, state)
#             return
#         if len(existing_random_v_notes_id) <= 1:
#             await message.message.edit_text(text='У вибірці має бути мінімум 2 відеоповідомлення.\n'
#                                                  'Надішліть ще номер(-и) відеоповідомлень:',
#                                             reply_markup=random_v_note_kb)
#         else:
#             await FSMClient.time_random_video_notes.set()
#             await message.message.edit_text(text='Рандомні відеоповідомлення збережено.\n'
#                                                  'Оберіть час, коли вони будуть публікуватись:',
#                                             reply_markup=await FullTimePicker().start_picker())


async def pick_time_random_v_notes(callback_query: types.CallbackQuery, callback_data: dict, state: FSMContext):
    r = await FullTimePicker().process_selection(callback_query, callback_data)
    await callback_query.answer()
    if r.status.name == 'CANCELED':
        await number_of_random_videos(callback_query, state)
        return
    if r.selected:
        data = await state.get_data()
        job_id = data.get('job_id')
        if job_id:
            job = scheduler.get_job(job_id)
            job_data = job.kwargs.get('data')
            job_data['time_random_video_notes'] = r.time
            job.modify(kwargs={'data': job_data})
        else:
            await state.update_data(time_random_video_notes=r.time)
            data = await state.get_data()
            scheduler.add_job(send_v_notes_cron, trigger='cron', hour=r.time.hour, minute=r.time.minute,
                              kwargs={'data': data})

        selected_time_str = r.time.strftime("%H:%M")
        await callback_query.message.answer(
            f'Відеоповідомлення будуть публікуватись кожного дня о {selected_time_str}.',
            reply_markup=change_create_post_kb
        )


async def number_of_random_photos(message, state: FSMContext):
    if isinstance(message, types.CallbackQuery):
        await FSMClient.random_or_self.set()
        try:
            await message.message.edit_text(
                text='"Рандом медіа" - медіа будуть міксуватись у пості.\n'
                     '"Рандом кругляши" - функція працює при зацикленні. Обрані відеоповідомлення будуть публікуватись кожного дня по черзі.',
                reply_markup=self_or_random_kb)
        except:
            pass
        return

    elif isinstance(message, types.Message):
        data = await state.get_data()
        job_id = data.get('job_id')

        if job_id:
            job = scheduler.get_job(job_id)
            data = job.kwargs.get('data')

        if data.get('loaded_post_files'):
            await message.answer(text='⚠️ Ручні налаштування медіа - скинуті')
            if job_id:
                data['loaded_post_files'] = None
                job.modify(kwargs={'data': data})
            else:
                await state.update_data(loaded_post_files=None)

        cat_name = data.get('choose_catalog')
        cat_data = get_catalog(cat_name)
        await state.update_data(random_photos_number=message.text)
        await message.answer(text='Фото додано у рандомну вибірку.')

        if cat_data.get('videos'):
            await FSMClient.number_of_rand_video.set()
            await message.answer(text=f'Скільки відео буде у вибірці? (доступно {len(cat_data.get("videos"))})',
                                 reply_markup=back_kb)
        else:
            await formatting_main_menu(message, state)


async def number_of_random_videos(message, state: FSMContext):
    if isinstance(message, types.CallbackQuery):
        await FSMClient.random_or_self.set()
        try:
            await message.message.edit_text(
                text='Якщо хочете щоб медіа обирались для посту автоматично - оберіть "Рандом медіа".',
                reply_markup=self_or_random_kb)
        except:
            await message.message.answer(
                text='Якщо хочете щоб медіа обирались для посту автоматично - оберіть "Рандом медіа".',
                reply_markup=self_or_random_kb)
        return
    await state.update_data(random_videos_number=message.text)
    await show_post(message, state)
    await message.answer(text='Відео додано у рандомну вибірку.', reply_markup=post_formatting_kb)
    await state.reset_state(with_data=False)

    # if post_type == 'looped':
    #     await post_looping(message, state)
    # elif post_type == 'planned':
    #     await nav_cal_handler(message, state)
    # elif post_type == 'now':
    #     await post_now_menu_handler(message, state)


async def inlines(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    try:
        await call.message.edit_text(text='Бажаєте додати чи видалити інлайн до посту?', reply_markup=inlines_menu_kb)
    except:
        pass


async def add_inline(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    data = await state.get_data()
    job_id = data.get('job_id')
    if job_id:
        data = scheduler.get_job(job_id).kwargs.get('data')
    post_media_files = data.get('loaded_post_files')
    random_photos_number = data.get('random_photos_number')
    if random_photos_number:
        if int(random_photos_number) > 1:
            await call.message.answer('❌ Інлайн кнопку неожливо додати у пост.\n'
                                      'До більше ніж 1 медіа інлайн неможливо додати.\n'
                                      'Інлайн можна додавати до:\n'
                                      '<i>- тексту</i>\n'
                                      '<i>- 1 фото</i>\n'
                                      '<i>- 1 відео</i>\n'
                                      '<i>- відеоповідомлення</i>\n'
                                      '<i>- голосове повідомлення</i>\n', parse_mode='html',
                                      reply_markup=post_formatting_kb)
            return

    if post_media_files:
        if len(post_media_files.media) > 1:
            await call.message.answer('❌ Інлайн кнопку не додано у пост\n'
                                      'До згрупованих медіа інлайн неможливо додати.\n'
                                      'Інлайн можна додавати до:\n'
                                      '<i>- тексту</i>\n'
                                      '<i>- 1 фото</i>\n'
                                      '<i>- 1 відео</i>\n'
                                      '<i>- відеоповідомлення</i>\n'
                                      '<i>- голосове повідомлення</i>\n', parse_mode='html',
                                      reply_markup=post_formatting_kb)

            return

    await FSMClient.inline_text.set()
    try:
        await call.message.edit_text(text='Надішліть текст інлайну:', reply_markup=back_kb)
    except:
        pass


async def pick_inline_to_delete(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    fsm_data = await state.get_data()
    job_id = fsm_data.get('job_id')

    if job_id:
        job = scheduler.get_job(job_id)
        fsm_data = job.kwargs.get('data')

    post_inlines: InlineKeyboardMarkup = fsm_data.get('inline_kb')
    if post_inlines and post_inlines.inline_keyboard:
        kb = InlineKeyboardMarkup()
        for inline in post_inlines.inline_keyboard:
            inline_index = post_inlines.inline_keyboard.index(inline)
            kb.add(InlineKeyboardButton(text=f"{inline[0].text}",
                                        callback_data=str(inline_index)))
        await call.message.answer(text='Оберіть інлайн, який хочете видалити.', reply_markup=kb)
        await FSMClient.inline_to_delete.set()
    else:
        try:
            await call.message.edit_text('У пості немає інлайнів', reply_markup=post_formatting_kb)
        except:
            pass


async def delete_inline(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    job_id = data.get('job_id')
    if job_id:
        data = scheduler.get_job(job_id).kwargs.get('data')
    kb: InlineKeyboardMarkup = data.get('inline_kb')
    message_data = call.data
    del kb.inline_keyboard[int(message_data)]
    if job_id:
        job = scheduler.get_job(job_id)
        data['inline_kb'] = kb
        job.modify(kwargs={'data': data})
    else:
        await state.update_data(inline_kb=kb)
    await show_post(call, state)
    await call.message.edit_text(text='Інлайн видалено.', reply_markup=post_formatting_kb)
    await state.reset_state(with_data=False)


async def inline_text_load(message, state: FSMContext):
    if isinstance(message, types.CallbackQuery):  # if back button
        if message.data == 'back':
            await state.reset_state(with_data=False)
            await inlines(message, state)
            return
    elif isinstance(message, types.Message):
        await state.update_data(inline_text=message.text)
        await message.answer(text='Надішліть посилання, яке бажаєте прикріпити до інлайну:', reply_markup=back_kb)
        await FSMClient.inline_link.set()


async def inline_link_load(message: types.Message, state: FSMContext):
    if 'entities' in message:
        if message.entities[0]['type'] == 'url':
            url = message.text

            data = await state.get_data()
            job_id = data.get('job_id')
            if job_id:
                job = scheduler.get_job(job_id)
                data = job.kwargs.get('data')

            # показати пост
            post_media_files = data.get('loaded_post_files')
            post_voice = data.get('voice')
            video_note = data.get('video_note')
            text = data.get('post_text')
            inline_text = data.get('inline_text')
            inline_kb: InlineKeyboardMarkup = data.get('inline_kb')

            if not inline_kb:
                if inline_text and url:
                    inline_kb = InlineKeyboardMarkup()
                    inline_kb.add(InlineKeyboardButton(text=inline_text, url=url))
                    await state.update_data(inline_kb=inline_kb)
            elif inline_kb:
                if inline_text and url:
                    inline_kb.add(InlineKeyboardButton(text=inline_text, url=url))
                    await state.update_data(inline_kb=inline_kb)

            if post_media_files:
                if len(post_media_files.media) == 1:
                    if post_media_files.media[0]['type'] == 'photo':
                        await message.answer_photo(photo=post_media_files.media[0]['media'],
                                                   caption=text,
                                                   reply_markup=inline_kb)
                    elif post_media_files.media[0]['type'] == 'video':
                        await message.answer_video(video=post_media_files.media[0]['media'],
                                                   caption=text,
                                                   reply_markup=inline_kb)

            elif post_voice:
                await message.answer_voice(voice=post_voice, caption=text, reply_markup=inline_kb)
            elif video_note:
                await message.answer_video_note(video_note=video_note, reply_markup=inline_kb)
            elif text:
                await message.answer(text=text, reply_markup=inline_kb)
            await message.answer('✅ Інлайн кнопку додано у пост', reply_markup=post_formatting_kb)

            await state.reset_state(with_data=False)
    else:
        await message.answer(text='Невірний формат.\n'
                                  'Потрібно надіслати саме посилання:')


async def reset_post(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    try:
        await call.message.edit_text(text='✅ Налаштування посту скинуто.', reply_markup=change_create_post_kb)
    except:
        pass


async def my_posts_menu(message, state: FSMContext):
    await FSMClient.all_posts_channel_id.set()

    if get_all_channels(message.from_user.id):
        kb = await kb_channels(message, bot)
        kb.add(back_to_main_menu)

        if isinstance(message, types.Message):
            if get_all_channels(message.from_user.id):
                await message.answer(text='Оберіть канал, щоб переглянути заплановані або зациклені пости:',
                                     reply_markup=kb)
            else:
                await message.answer(text='У вас немає каналів.')
                await add_channel(message, state)

        elif isinstance(message, types.CallbackQuery):
            await message.answer()
            if get_all_channels(message.from_user.id):
                await message.message.answer(text='Оберіть канал, щоб переглянути заплановані або зациклені пости:',
                                             reply_markup=kb)
            else:
                await message.message.answer(text='У вас немає каналів.')
                await add_channel(message, state)
    else:
        kb = InlineKeyboardMarkup().add(create_post_inline)
        await message.answer(text='❌ У вас немає постів.', reply_markup=kb)


async def load_channel_id_enter_date(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    all_jobs = scheduler.get_jobs()
    channel_id = call.data
    if all_jobs:
        jobs_in_channel = [job.kwargs.get('data') for job in all_jobs if
                           channel_id in job.kwargs.get('data').get('channel_id')]
        if jobs_in_channel:
            await state.update_data(all_posts_channel_id=channel_id)
            await FSMClient.posts_by_data.set()
            await call.message.edit_text(text='Оберіть дату посту:',
                                         reply_markup=await SimpleCalendar().start_calendar())
        else:
            try:
                await call.message.edit_text(text='Немає запланованих або зациклених постів.',
                                             reply_markup=InlineKeyboardMarkup().add(create_post_inline))
            except:
                pass
    else:
        try:
            await call.message.edit_text(text='Немає запланованих або зациклених постів.',
                                         reply_markup=InlineKeyboardMarkup().add(create_post_inline))
        except:
            pass


async def my_posts_by_date(callback_query: types.CallbackQuery, callback_data: dict, state: FSMContext):
    selected, date = await SimpleCalendar().process_selection(callback_query, callback_data)
    data = await state.get_data()
    if selected:
        jobs_in_channel = job_list_by_channel(data=data, date=date)
        kb = InlineKeyboardMarkup()
        jobs_in_channel = sorted(jobs_in_channel, key=sorting_key_jobs)
        for job_in_channel in jobs_in_channel:
            job_in_channel_data = job_in_channel.kwargs.get('data')
            post_type = job_in_channel_data.get('post_type')
            if post_type == 'planned':
                time_planning: datetime.time = job_in_channel.next_run_time.strftime('%H:%M')
                kb.add(
                    InlineKeyboardButton(text=f"Пост о {time_planning} - {job_in_channel_data.get('post_text')}",
                                         callback_data=job_in_channel.id))
            else:
                time_loop: datetime.time = job_in_channel.next_run_time.strftime('%H:%M')
                random_v_note_loop: datetime.time = job_in_channel_data.get('time_random_video_notes')
                if time_loop:
                    kb.add(
                        InlineKeyboardButton(
                            text=f"Пост о {time_loop} - {job_in_channel_data.get('post_text')}",
                            callback_data=job_in_channel.id))
                elif random_v_note_loop:
                    kb.add(
                        InlineKeyboardButton(text=f"Відеоповідомлення о {random_v_note_loop.strftime('%H:%M')}",
                                             callback_data=job_in_channel.id))
        # add_posts_to_kb(jobs_in_channel, kb)
        kb.add(back_to_my_posts_inline)
        await FSMClient.job_id.set()
        try:
            await callback_query.message.edit_text(
                text=f'Ваші заплановані та зациклені пости {date.strftime("%d.%m.%y")}.\n'
                     'Оберіть будь-який, щоб змінити.', reply_markup=kb)
        except:
            await callback_query.message.answer(
                text=f'Ваші заплановані та зациклені пости {date.strftime("%d.%m.%y")}.\n'
                     'Оберіть будь-який, щоб змінити.', reply_markup=kb)


def register_handlers_client(dp: Dispatcher):
    dp.middleware.setup(AuthMiddleware())
    dp.register_message_handler(start_command, commands=['start'], state='*')
    dp.register_message_handler(edit_create_post_channel_list, Text(equals='Створити пост'), state="*")
    dp.register_callback_query_handler(edit_create_post_channel_list, Text(equals='Створити пост'), state="*")
    dp.register_callback_query_handler(main_menu, Text(equals='main_menu'), state="*")
    dp.register_message_handler(edit_create_post_channel_list, Text(equals='Змінити пост'), state="*")
    dp.register_callback_query_handler(edit_create_post_channel_list, Text(equals='Змінити пост'), state="*")
    dp.register_message_handler(media_base_panel, Text(equals='База медіа'), state='*')
    dp.register_message_handler(signal_menu, Text(equals='📣 Сигнали'), state='*')
    dp.register_callback_query_handler(signal_menu, Text(equals='📣 Сигнали'), state='*')
    dp.register_message_handler(my_posts_menu, Text(equals='Мої пости'), state='*')
    dp.register_callback_query_handler(my_posts_menu, Text(equals='Мої пости'), state='*')
    dp.register_callback_query_handler(load_channel_id_enter_date, state=FSMClient.all_posts_channel_id)
    dp.register_callback_query_handler(my_posts_by_date, simple_cal_callback.filter(),
                                       state=FSMClient.posts_by_data)

    dp.register_callback_query_handler(reset_post, Text(equals='reset_post'), state='*')

    dp.register_callback_query_handler(edit_post_list, state=FSMClient.channel_change_post)
    dp.register_message_handler(edit_post_list, state=FSMClient.channel_change_post)
    dp.register_message_handler(add_channel, commands=['addchannel'], state='*')
    dp.register_message_handler(channel_manage_menu, Text(equals='Канали'), state='*')
    dp.register_callback_query_handler(deny_channel, Text(equals='Видалити канал'))
    dp.register_message_handler(remove_channel_id, state=FSMClient.remove_channel_id)

    dp.register_callback_query_handler(channel_list, Text(equals='Список каналів'))
    dp.register_callback_query_handler(add_channel, Text(equals='Додати канал'), state=None)
    dp.register_message_handler(load_channel_id, state=FSMClient.channel_id, content_types=types.ContentType.all())
    dp.register_callback_query_handler(enter_change_text, state=FSMClient.create_post_in_channel)
    dp.register_message_handler(load_changed_text, state=FSMClient.post_text)
    dp.register_callback_query_handler(load_changed_text, state=FSMClient.post_text)
    dp.register_callback_query_handler(formatting_main_menu, Text(equals='formatting_main_menu'))

    # dp.register_callback_query_handler(post_now_menu_handler, Text(equals='post_now_menu'))
    dp.register_callback_query_handler(make_post_now, Text(equals='Опублікувати'))
    dp.register_callback_query_handler(del_post, Text(equals='delete_post'))
    dp.register_message_handler(load_media_file,
                                state=FSMClient.loaded_post_files,
                                content_types=types.ContentType.all())
    dp.register_callback_query_handler(load_media_file, state=FSMClient.loaded_post_files)
    dp.register_callback_query_handler(choose_or_self_media, Text(equals='Налаштувати медіа'))
    dp.register_callback_query_handler(load_media_answer, state=FSMClient.media_answer)
    dp.register_callback_query_handler(change_job, state=FSMClient.job_id)

    dp.register_callback_query_handler(enter_change_text, Text(equals='Змінити текст'))
    dp.register_callback_query_handler(del_voice_or_video_note, state=FSMClient.del_voice_or_vnote_answer)
    dp.register_message_handler(del_media, state=FSMClient.del_media_answer)
    dp.register_callback_query_handler(del_media, state=FSMClient.del_media_answer)

    dp.register_message_handler(number_of_random_photos, state=FSMClient.number_of_rand_photo)
    dp.register_callback_query_handler(number_of_random_photos, state=FSMClient.number_of_rand_photo)
    dp.register_message_handler(number_of_random_videos, state=FSMClient.number_of_rand_video)
    dp.register_callback_query_handler(number_of_random_videos, state=FSMClient.number_of_rand_video)
    dp.register_callback_query_handler(random_or_self, state=FSMClient.random_or_self)

    dp.register_callback_query_handler(inlines, Text(equals='inlines'))
    dp.register_callback_query_handler(add_inline, Text(equals='add_inline'))
    dp.register_callback_query_handler(pick_inline_to_delete, Text(equals='del_inline'))
    dp.register_message_handler(inline_text_load, state=FSMClient.inline_text)
    dp.register_callback_query_handler(inline_text_load, state=FSMClient.inline_text)
    dp.register_message_handler(inline_link_load, state=FSMClient.inline_link)
    dp.register_callback_query_handler(inline_link_load, state=FSMClient.inline_link)
    dp.register_callback_query_handler(delete_inline, state=FSMClient.inline_to_delete)

    # dp.register_message_handler(load_random_v_notes_id, state=FSMClient.random_v_notes_id)
    # dp.register_callback_query_handler(load_random_v_notes_id, state=FSMClient.random_v_notes_id)
    dp.register_callback_query_handler(pick_time_random_v_notes, full_timep_callback.filter(),
                                       state=FSMClient.time_random_video_notes)
