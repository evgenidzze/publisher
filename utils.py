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

from create_bot import bot, scheduler
from json_functionality import get_all_channels, get_users_dict, get_catalog
from aiogram.dispatcher.middlewares import BaseMiddleware
import io
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from keyboards.kb_client import create_catalogs_kb

aiogram_timepicker.panel.full._default['select'] = 'Обрати'
aiogram_timepicker.panel.full._default['cancel'] = 'Скасувати'


class AuthMiddleware(BaseMiddleware):
    async def on_pre_process_update(self, update: types.Update, data: dict):
        if not isinstance(update.message, type(None)):
            if update.callback_query:
                if str(update.callback_query.from_user.id) not in get_users_dict():
                    await update.callback_query.message.answer(
                        text='У вас немає доступу до бота. Після отримання доступу від адміністратора, натисніть на команду /start',
                        reply_markup=ReplyKeyboardRemove())
                    raise CancelHandler()
            else:
                if str(update.message.from_user.id) not in get_users_dict():
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
        texts = await get_catalog(catalog_for_text)
        texts = texts.get('texts')
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
    all_channels_list = get_all_channels(message.from_user.id)
    kb_channels_list = []

    if all_channels_list:

        for channel_id in all_channels_list:
            channel = await bot.get_chat(channel_id)
            channel_name = channel.title
            kb_channels_list.append(InlineKeyboardButton(text=channel_name, callback_data=channel_id))
        kb_all_channels.add(*kb_channels_list)
        return kb_all_channels
    else:
        print('all_channels_list is empty in def kb_channels')


def del_list_duplicates(l: list) -> list:
    seen_ids = set()
    result = []
    for item in l:
        unique_id = item["photo"][0]["file_unique_id"]
        if unique_id not in seen_ids:
            seen_ids.add(unique_id)
            result.append(item)
    return result


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


async def show_cat_content(message, catalog_data: dict, media_type: str = None):
    if isinstance(message, types.CallbackQuery):
        message = message.message
    for media in catalog_data:
        if media == 'videos':
            if media == media_type:
                for video_num in range(len(catalog_data[media])):
                    await message.answer_video(video=catalog_data[media][video_num], caption=str(video_num + 1))
                return
            elif not media_type:
                for video in catalog_data[media]:
                    await message.answer_video(video=video)
        elif media == 'photos':
            if media == media_type:
                for photo_num in range(len(catalog_data[media])):
                    await message.answer_photo(photo=catalog_data[media][photo_num], caption=str(photo_num + 1))
                return
            elif not media_type:
                for photo in catalog_data[media]:
                    await message.answer_photo(photo=photo)
        elif media == 'voices':
            if media == media_type:
                for voice_num in range(len(catalog_data[media])):
                    await message.answer_voice(voice=catalog_data[media][voice_num], caption=str(voice_num + 1))
                return
            elif not media_type:
                for voice in catalog_data[media]:
                    await message.answer_voice(voice=voice)
        elif media == 'documents':
            if media == media_type:
                for document_num in range(len(catalog_data[media])):
                    await message.answer_document(document=catalog_data[media][document_num],
                                                  caption=str(document_num + 1))
                return
            elif not media_type:
                for document in catalog_data[media]:
                    await message.answer_document(document=document)
        elif media == 'gifs':
            if media == media_type:
                for gif_num in range(len(catalog_data[media])):
                    await message.answer_animation(animation=catalog_data[media][gif_num],
                                                   caption=str(gif_num + 1))
                return
            elif not media_type:
                for gif in catalog_data[media]:
                    await message.answer_animation(animation=gif)

        elif media == 'video_notes':
            if media == media_type:
                for video_note_num in range(len(catalog_data[media])):
                    await message.answer_video_note(video_note=catalog_data[media][video_note_num])
                    await message.answer(text=str(video_note_num + 1))
                return
            elif not media_type:
                for video_note in catalog_data[media]:
                    await message.answer_video_note(video_note=video_note)
        elif media == 'texts':
            if media == media_type:
                for text_num in range(len(catalog_data[media])):
                    message = await message.answer(text=catalog_data[media][text_num])
                    await message.reply(text=str(text_num + 1))
            elif not media_type:
                for text in catalog_data[media]:
                    await message.answer(text=text)


def get_random_photos(count, cat_name) -> list:
    with open('data.json', 'r', encoding='utf-8') as file:
        file_data = json.load(file)
        res = []
        photos_id = file_data['catalogs'][cat_name]['photos']
        random.shuffle(photos_id)
        for i in range(count):
            res.append(photos_id[i])
        return res


def get_random_videos(count, cat_name) -> list:
    with open('data.json', 'r', encoding='utf-8') as file:
        file_data = json.load(file)
        res = []
        print(cat_name)
        videos_id = file_data['catalogs'][cat_name]['videos']

        random.shuffle(videos_id)
        for i in range(count):
            res.append(videos_id[i])
        return res


def get_random_gifs(count, cat_name) -> list:
    with open('data.json', 'r', encoding='utf-8') as file:
        file_data = json.load(file)
        res = []
        gifs_id = file_data['catalogs'][cat_name]['documents']
        gifs_id.extend(file_data['catalogs'][cat_name]['gifs'])

        random.shuffle(gifs_id)
        for i in range(1):
            res.append(gifs_id[i])
        return res


def is_float_int(string: str):
    string = string.replace(',', '.')
    try:
        float(string)
        return True
    except ValueError:
        return False


one_to_ten_uz = {
    1: "Birinchi signal",
    2: "Ikkinchi signal",
    3: "Uchinchi signal",
    4: "To'rtinchi signal",
    5: "Beshinchi signal",
    6: "Oltinchi signal",
    7: "Ettinchi signal",
    8: "Sakkizinchi signal",
    9: "To'qqizinchi signal",
    10: "O'ninchi signal"
}

one_to_ten_br = {
    1: "Primeiro signal",
    2: "Segundo signal",
    3: "Terceiro signal",
    4: "Quarto signal",
    5: "Quinto signal",
    6: "Sexto signal",
    7: "Sétimo signal",
    8: "Oitavo signal",
    9: "Nono signal",
    10: "Décimo signal"
}


async def cron_signals(data):
    signal_channel_id = data.get('signal_channel_id')
    signal_bet = data.get('signal_bet')
    signals_count = data.get('signals_count')
    signal_period_minutes = data.get('signal_period_minutes')
    signal_location = data.get('signal_location')

    koef_font = ImageFont.truetype('./media/fonts/Roboto-Bold.ttf', 22)
    win_sum_font = ImageFont.truetype('./media/fonts/arialbd.ttf', 22)

    for signal_num in range(int(signals_count)):
        if signal_location == 'uz':
            i = Image.open('media/proove_uz.png')
            text = (f'🚨⚡️ BOT {one_to_ten_uz[signal_num + 1]} signal berdi 🤖\n\n'
                    f"🛫 Stavka qilaman: {signal_bet} so'm")

        else:
            i = Image.open('media/proove_br.png')
            text = (f'🚨⚡️ {one_to_ten_br[signal_num + 1]} sinal do canal VIP! 🤖\n\n'
                    f'🛫 Minha aposta: {signal_bet} reais')

        from driver import wait_for_new_coef
        coef = float(await wait_for_new_coef()) - 0.12

        Im = ImageDraw.Draw(i)

        await bot.send_message(chat_id=signal_channel_id, text=text)
        # await asyncio.sleep(15)

        win_sum = (int(signal_bet) * coef)
        Im.text((88, 43), f"{format(coef, '.2f')}x", fill=(220, 220, 220), font=koef_font)
        Im.text((280, 62), f"{format(win_sum, '.2f')}", fill=(240, 240, 240), font=win_sum_font, anchor='mb')

        image_buffer = io.BytesIO()
        i.save(image_buffer, format='PNG')  # You can change the format as needed

        image_buffer.seek(0)

        await bot.send_photo(chat_id=signal_channel_id, photo=image_buffer)
        await asyncio.sleep(int(signal_period_minutes))


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
        await bot.send_message(chat_id=chat_id, text=text, reply_markup=randomed_text_kb, parse_mode='Markdown')


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
