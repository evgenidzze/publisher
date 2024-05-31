import asyncio
import datetime
import json
import logging
import random

import aiogram_timepicker
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.handler import CancelHandler
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from aiogram.utils.exceptions import CantParseEntities

from create_bot import bot, scheduler
from json_functionality import get_all_channels, get_all_catalog_media, get_user, get_media_by_type
from aiogram.dispatcher.middlewares import BaseMiddleware
from keyboards.kb_client import create_catalogs_kb

aiogram_timepicker.panel.full._default['select'] = 'Обрати'
aiogram_timepicker.panel.full._default['cancel'] = 'Скасувати'


class AuthMiddleware(BaseMiddleware):
    async def on_pre_process_update(self, update: types.Update, data: dict):
        if not isinstance(update.message, type(None)):
            if update.callback_query:
                user = await get_user(update.callback_query.from_user.id)
                if not user:
                    await update.callback_query.message.answer(
                        text='У вас немає доступу до бота. Після отримання доступу від адміністратора, натисніть на команду /start',
                        reply_markup=ReplyKeyboardRemove())
                    raise CancelHandler()
            else:
                user = await get_user(update.message.from_user.id)
                if not user:
                    await update.message.answer(
                        text='У вас немає доступу до бота. Після отримання доступу від адміністратора, натисніть на команду /start',
                        reply_markup=ReplyKeyboardRemove())
                    raise CancelHandler()


def pressed_back_button(message):
    if isinstance(message, types.CallbackQuery):
        call: types.CallbackQuery = message
        if call.data == 'back':
            return True
        else:
            return False


def add_random_media(media_files, data, cat_name):
    random_photos_number = data.get('random_photos_number')
    random_videos_number = data.get('random_videos_number')
    random_gifs_number = data.get('random_gifs_number')

    if random_photos_number:
        r_photos = get_random_photos(count=int(random_photos_number), cat_name=cat_name)
        for rand_photo in r_photos:
            media_files.attach_photo(rand_photo)

    if random_videos_number:
        r_videos = get_random_videos(count=int(random_videos_number), cat_name=cat_name)
        for rand_video in r_videos:
            media_files.attach_video(rand_video)

    if random_gifs_number:
        r_gifs = get_random_gifs(count=int(random_gifs_number), cat_name=cat_name)
        for rand_gifs in r_gifs:
            media_files.attach_video(rand_gifs)


async def send_message_time(data):
    channel_id = data.get('channel_id')
    voice = data.get('voice')
    video_note = data.get('video_note')
    kb_inline = data.get('inline_kb')
    post_text = await create_text(data)
    kb = await create_kb(kb_inline)
    media_files = await create_random_media(data)
    await send_post_to_channel(post_media_files=media_files, post_text=post_text, bot_instance=bot,
                               channel_id=channel_id,
                               post_voice=voice,
                               post_video_note=video_note,
                               inline_kb=kb)


async def send_message_cron(data):
    kb_inline = data.get('inline_kb')
    skip_minutes_loop = data.get('skip_minutes_loop')
    post_text = await create_text(data)
    kb = await create_kb(kb_inline)
    media_files = await create_random_media(data)

    if data.get('video_note'):
        post_video_note = data.get('video_note')
    else:
        post_video_note = data.get('random_v_notes_id')
        if post_video_note:
            post_video_note = post_video_note[0]

    if skip_minutes_loop:
        if skip_minutes_loop == '0':
            random_number = 0
        else:
            random_minutes = data.get('skip_minutes_loop').split('-')
            from_minute = int(random_minutes[0])
            to_minute = int(random_minutes[1])
            random_number = random.randint(from_minute, to_minute)
    else:
        random_number = 4
    print(f"post in {random_number} minutes")
    await asyncio.sleep(random_number * 60)
    await send_post_to_channel(post_media_files=media_files, post_text=post_text, bot_instance=bot,
                               channel_id=data.get('channel_id'), post_voice=data.get('voice'),
                               post_video_note=post_video_note,
                               inline_kb=kb, data=data)


async def create_text(data):
    post_text = '' if not data.get("post_text") else data.get('post_text')
    text_index = data.get('text_index')
    catalog_for_text = data.get('catalog_for_text')
    if catalog_for_text:
        texts = await get_media_by_type(catalog_for_text, media_type='text')
        texts = [text.text for text in texts]
        if text_index:
            post_text = texts[int(text_index) - 1]
        else:
            post_text = random.choice(texts)
    elif isinstance(post_text, list):
        post_text = random.choice(post_text)
    return post_text


async def send_v_notes_cron(data):
    channel_id = data.get('channel_id')
    random_v_notes_id: list = data.get('random_v_notes_id')
    await bot.send_video_note(chat_id=channel_id, video_note=random_v_notes_id[0])
    data['random_v_notes_id'].append(random_v_notes_id[0])
    del data['random_v_notes_id'][0]


async def kb_channels(message, bot):
    kb_all_channels = InlineKeyboardMarkup(row_width=1)
    all_channels_list = await get_all_channels(message.from_user.id)
    kb_channels_list = []
    if all_channels_list:
        for channel in all_channels_list:
            kb_channels_list.append(InlineKeyboardButton(text=channel.name, callback_data=channel.channel_id))
        kb_all_channels.add(*kb_channels_list)
        return kb_all_channels
    else:
        print('all_channels_list is empty in def kb_channels')


async def send_voice_from_audio(message: types.Message, bot):
    file_info = await bot.get_file(message.audio.file_id)
    downloaded_file = await bot.download_file(file_info.file_path)
    return await message.answer_voice(downloaded_file)


async def restrict_media(messages, state, data, post_formatting_kb):
    # якщо надсилаємо (відео фото документ) при цьому войс у даних - заборонити
    if messages[0].content_type in ('video', 'photo', 'document') and 'voice' in data:
        await messages[0].answer(text='❌ Голосове повідомлення не можна публікувати у групі з іншими медіа',
                                 reply_markup=post_formatting_kb)
        await state.reset_state(with_data=False)
        return True
    if messages[0].content_type in ('audio', 'voice'):
        if 'loaded_post_files' in data:
            await messages[0].answer(text='❌ Голосове повідомлення не можна публікувати у групі з іншими медіа',
                                     reply_markup=post_formatting_kb)
            await state.reset_state(with_data=False)
            return True

        if len(messages) > 1:
            await messages[0].answer(text='❌ У пості може бути тільки 1 голосове.',
                                     reply_markup=post_formatting_kb)
            await state.reset_state(with_data=False)
            return True
    if data.get('voice'):
        await messages[0].answer(text='❌ У пості може бути тільки 1 голосове.',
                                 reply_markup=post_formatting_kb)
        await state.reset_state(with_data=False)
        return True


def set_caption(media, text):
    for m in range(len(media.media)):
        if m > 0:
            if 'caption' in media.media[m]:
                media.media[m].caption = None
        else:
            media.media[m].caption = text
            media.media[m].parse_mode = 'Markdown'


async def send_post_to_channel(post_media_files: types.MediaGroup, post_text, bot_instance, channel_id, post_voice,
                               post_video_note,
                               inline_kb, data=None):
    if post_media_files:
        set_caption(text=post_text, media=post_media_files),
        if len(post_media_files.media) == 1:
            if post_media_files.media[0]['type'] == 'photo':
                await bot.send_photo(chat_id=channel_id, photo=post_media_files.media[0]['media'],
                                     caption=post_text,
                                     reply_markup=inline_kb, parse_mode='Markdown')
            elif post_media_files.media[0]['type'] == 'video':
                await bot.send_video(chat_id=channel_id, video=post_media_files.media[0]['media'],
                                     caption=post_text,
                                     reply_markup=inline_kb, parse_mode='Markdown')
            elif post_media_files.media[0]['type'] == 'document':
                await bot.send_document(chat_id=channel_id,
                                        document=post_media_files.media[0]['media'],
                                        caption=post_text,
                                        reply_markup=inline_kb, parse_mode='Markdown')
        else:
            await bot.send_media_group(chat_id=channel_id, media=post_media_files)
    elif post_voice:
        await bot.send_voice(chat_id=channel_id, voice=post_voice, caption=post_text,
                             reply_markup=inline_kb)
    elif post_video_note:
        await bot.send_video_note(chat_id=channel_id, video_note=post_video_note, reply_markup=inline_kb)
    else:
        await bot.send_message(chat_id=channel_id, text=post_text, reply_markup=inline_kb,
                               disable_web_page_preview=True, parse_mode='Markdown')
    logging.info(f'POST SENT; DATA: {data}')


async def show_cat_content(message, catalog_data: dict):
    if isinstance(message, types.CallbackQuery):
        message = message.message
    for media in catalog_data:
        if media.media_type == 'video':
            await message.answer_video(video=media.file_id, caption=str(media.id))
        elif media.media_type == 'photo':
            await message.answer_photo(photo=media.file_id, caption=str(media.id))
        elif media.media_type == 'voice':
            await message.answer_voice(voice=media.file_id, caption=str(media.id))
        elif media.media_type == 'document':
            await message.answer_document(document=media.file_id,
                                          caption=str(media.id))

        elif media.media_type == 'gif':
            await message.answer_animation(animation=media.file_id,
                                           caption=str(media.id))
        elif media.media_type == 'video_note':
            await message.answer_video_note(video_note=media.file_id)
            await message.answer(text=str(media.id))
        elif media.media_type == 'text':
            message = await message.answer(text=media.text)
            await message.reply(text=str(media.id))


async def show_media_by_type(message, cat_id, media_type):
    if isinstance(message, types.CallbackQuery):
        message = message.message
    media = await get_media_by_type(cat_id, media_type)
    send_functions = {
        'video': message.answer_video,
        'photo': message.answer_photo,
        'voice': message.answer_voice,
        'document': message.answer_document,
        'gif': message.answer_animation,
        'video_note': message.answer_video_note,
        'text': lambda text: message.answer(text.text)
    }
    send_function = send_functions.get(media_type)
    if send_function:
        for item in media:
            if media_type == 'text':
                await send_function(item)
            elif media_type == 'video_note':
                video_message = await send_function(item.file_id)
                await video_message.reply(text=item.id)
            else:
                await send_function(item.file_id, caption=item.id)


def get_random_photos(count, cat_name) -> list:
    with open('../data.json', 'r', encoding='utf-8') as file:
        file_data = json.load(file)
        res = []
        photos_id = file_data['catalogs'][cat_name]['photos']
        random.shuffle(photos_id)
        for i in range(count):
            res.append(photos_id[i])
        return res


def get_random_videos(count, cat_name) -> list:
    with open('../data.json', 'r', encoding='utf-8') as file:
        file_data = json.load(file)
        res = []
        videos_id = file_data['catalogs'][cat_name]['videos']

        random.shuffle(videos_id)
        for i in range(count):
            res.append(videos_id[i])
        return res


def get_random_gifs(count, cat_name) -> list:
    with open('../data.json', 'r', encoding='utf-8') as file:
        file_data = json.load(file)
        res = []
        gifs_id = file_data['catalogs'][cat_name]['documents']
        gifs_id.extend(file_data['catalogs'][cat_name]['gifs'])

        random.shuffle(gifs_id)
        for i in range(1):
            res.append(gifs_id[i])
        return res


def sorting_key_jobs(job):
    next_run: datetime.datetime = job.next_run_time
    return next_run.time()


async def show_post(message, state: FSMContext):
    data = await state.get_data()
    job_id = data.get('job_id')
    if job_id:
        job = scheduler.get_job(job_id)
        data = job.kwargs.get('data')
    post_media_files = data.get('loaded_post_files')
    kb_inline: InlineKeyboardMarkup = data.get('inline_kb')
    randomed_text_kb = InlineKeyboardMarkup()
    if kb_inline:
        for buttons in kb_inline.inline_keyboard:
            for button in buttons:
                randomed_text_kb.add(InlineKeyboardButton(text=random.choice(button.text), url=button.url))
    post_voice = data.get('voice')
    video_note = data.get('video_note')
    random_v_notes_id = data.get('random_v_notes_id')
    chat_id = message.from_user.id
    text = data.get('post_text') if data.get('post_text') else ''
    text += f"\nКаталог: {data.get('choose_catalog')}" if data.get('choose_catalog') else ''
    if isinstance(text, list) or data.get('catalog_for_text'):
        if data.get('text_index'):
            text = await create_text(data)
        else:
            text = 'Текст буде обраний рандомно.'
            if data.get('cat_name'):
                text += f"Назва каталогу: \n\n{data.get('cat_name')}"
            elif data.get('catalog_for_text'):
                text += f"\n\nНазва каталогу: {data.get('catalog_for_text')}"

    if job_id:
        if scheduler.get_job(job_id).name == 'send_message_cron':
            text = (f"{text}\n"
                    "————————\n"
                    f"🌀")
        elif scheduler.get_job(job_id).name == 'send_message_time':
            text = (f"{text}\n"
                    "————————\n"
                    f"🗓")
    if post_media_files:
        if len(post_media_files.media) == 1:
            m = post_media_files.media[0]
            if m.type == 'video':
                await bot.send_video(chat_id=chat_id, video=m.media, caption=text, reply_markup=randomed_text_kb,
                                     parse_mode='Markdown')
            elif m.type == 'photo':
                await bot.send_photo(chat_id=chat_id, photo=m.media, caption=text, reply_markup=randomed_text_kb,
                                     parse_mode='Markdown')
            elif m.type == 'document':
                await bot.send_document(chat_id=chat_id, document=m.media, caption=text,
                                        reply_markup=randomed_text_kb, parse_mode='Markdown')
        else:
            set_caption(text=text, media=post_media_files),
            await bot.send_media_group(chat_id=chat_id, media=post_media_files)
    elif post_voice:
        await bot.send_voice(chat_id=chat_id, voice=post_voice, caption=text, reply_markup=randomed_text_kb)
    elif video_note:
        await bot.send_video_note(chat_id=chat_id, video_note=video_note, reply_markup=randomed_text_kb)
    elif random_v_notes_id:
        await bot.send_video_note(chat_id=chat_id, video_note=random.choice(random_v_notes_id),
                                  reply_markup=randomed_text_kb)
    elif text:
        try:
            await bot.send_message(chat_id=chat_id, text=text, reply_markup=randomed_text_kb, parse_mode='Markdown')
        except CantParseEntities as err:
            print(err)
            await bot.send_message(chat_id=chat_id, text=text, reply_markup=randomed_text_kb)


def job_list_by_channel(data, date: datetime.datetime):
    all_posts_channel_id = data.get('all_posts_channel_id')
    all_jobs = scheduler.get_jobs()
    jobs_in_channel = []
    for job in all_jobs:
        job_data = job.kwargs.get('data')
        if job_data.get('channel_id') == all_posts_channel_id:
            date_planning: datetime.datetime = job.next_run_time
            if date_planning:
                if date_planning.date() == date.date() or job.name == 'send_message_cron':
                    jobs_in_channel.append(job)
            else:
                jobs_in_channel.append(job)
    return jobs_in_channel


async def alert_vnote_text(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if data.get('post_text') and data.get('video_note'):
        await message.answer(text='⚠️ Текст з посту видалено.\n'
                                  '<i>Текст неможоливо додати до відеоповідомлення.</i>', parse_mode='html')


async def paginate(kb: types.InlineKeyboardMarkup):
    back_btn = InlineKeyboardButton(text='⬅️', callback_data='-')
    page_btn = InlineKeyboardButton(text='1', callback_data='1')
    next_btn = InlineKeyboardButton(text='➡️', callback_data='+')
    kb.add(back_btn, page_btn, next_btn)


async def create_kb(inline_kb):
    kb = InlineKeyboardMarkup()
    if inline_kb:
        for buttons in inline_kb.inline_keyboard:
            for button in buttons:
                kb.add(InlineKeyboardButton(text=random.choice(button.text), url=button.url))
    return kb


async def create_random_media(data):
    cat_name = data.get('catalog_for_text')
    if not cat_name:
        cat_name = data.get('choose_catalog')

    media_files = data.get('loaded_post_files')
    if not media_files and (
            data.get('random_photos_number') or data.get('random_videos_number') or data.get('random_gifs_number')):
        media_files = types.MediaGroup()
        add_random_media(media_files=media_files, data=data, cat_name=cat_name)
    return media_files


async def get_create_page_num(data, state):
    if not data.get('page_num'):
        await state.update_data(page_num=1)


async def catalog_paginate(state):
    data = await state.get_data()
    await get_create_page_num(data, state)
    data = await state.get_data()
    page_num = data.get('page_num')
    catalogs_kb = await create_catalogs_kb(page_num)
    await paginate(catalogs_kb)
    catalogs_kb.inline_keyboard[-1][-2].text = page_num
    return catalogs_kb


async def update_page_num(data, call, state):
    page_num = data.get('page_num')
    if page_num and call.data == '+':
        await state.update_data(page_num=page_num + 1)
    elif page_num and call.data == '-' and page_num > 1:
        await state.update_data(page_num=page_num - 1)
    elif not page_num:
        await state.update_data(page_num=1)


async def get_media_id(message: types.Message):
    if message.content_type == 'photo':
        return message.photo[0].file_id
    elif message.content_type == 'video':
        return message.video.file_id
    elif message.content_type == 'animation':
        return message.animation.file_id
    elif message.content_type in ('voice', 'audio', 'video_note'):
        if message.content_type == 'voice':
            return message.voice.file_id
        elif message.content_type == 'audio':
            await message.answer(text='Переформатування аудіо у голосове...')
            voice_message = await send_voice_from_audio(message=message, bot=bot)
            return voice_message.voice.file_id
        elif message.content_type == 'video_note':
            return message.video_note.file_id
    elif message.content_type == 'document':
        return message.document.file_id
