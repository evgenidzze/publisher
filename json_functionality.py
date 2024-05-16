import json
from typing import List

from aiogram import types

from keyboards.kb_admin import kb_manage_user
from keyboards.kb_client import kb_manage_channel_inline


def get_admins() -> list:
    with open('data.json', 'r', encoding='utf-8') as file:
        file_data = json.load(file)
        return file_data['admins']


def get_users_dict() -> dict:
    with open('data.json', 'r', encoding='utf-8') as file:
        file_data = json.load(file)
        return file_data['users']


async def save_user_id_to_json(user_id: str, message: types.Message):
    with open('data.json', 'r+', encoding='utf-8') as file:
        file_data = json.load(file)
        if user_id in file_data['users']:
            await message.answer(text=f'У користувача з id: {user_id} вже є доступ.', reply_markup=kb_manage_user)
        else:
            file_data['users'][user_id] = message.forward_from.username
            file.seek(0)
            json.dump(file_data, file, indent=4)
            await message.answer(text=f'Ви надали доступ користувачу {message.forward_from.username} з id: {user_id}',
                                 reply_markup=kb_manage_user)


async def remove_user_id_from_json(user_id, message: types.Message):
    with open('data.json', 'r', encoding='utf-8') as file:
        file_data = json.load(file)

    if user_id in file_data['users']:
        del file_data['users'][user_id]

        with open('data.json', 'w', encoding='utf-8') as file:
            json.dump(file_data, file, indent=4, ensure_ascii=False)

        await message.answer(text=f'Ви скасували права користувачу з id: {user_id}', reply_markup=kb_manage_user)
    else:
        await message.answer(text=f'Користувача з таким id не існує', reply_markup=kb_manage_user)


async def save_channel_json(channel_id: str, message: types.Message):
    with open('data.json', 'r+', encoding='utf-8') as file:
        file_data = json.load(file)
        user_id = str(message.from_user.id)
        channel_name = message.forward_from_chat.title

        if user_id not in file_data['channels']:  # if user don't have any channels
            file_data['channels'][user_id] = {channel_id: channel_name}
            file.seek(0)
            json.dump(file_data, file, indent=4)
            await message.answer(
                text=f'Канал <a href="{await message.forward_from_chat.get_url()}">{message.forward_from_chat.title}'
                     f'</a> з id: <code>{channel_id}</code> успішно підключений',
                reply_markup=kb_manage_channel_inline, parse_mode='html')
        else:
            if channel_id not in file_data['channels'][user_id]:
                file_data['channels'][user_id][channel_id] = channel_name
                file.seek(0)
                json.dump(file_data, file, indent=4)
                await message.answer(
                    text=f'Канал <a href="{await message.forward_from_chat.get_url()}">{message.forward_from_chat.title}'
                         f'</a> з id: <code>{channel_id}</code> успішно підключений',
                    reply_markup=kb_manage_channel_inline, parse_mode='html')
            else:
                await message.answer(
                    text=f'Канал <a href="{await message.forward_from_chat.get_url()}">{message.forward_from_chat.title}'
                         f'</a> з id: <code>{channel_id}</code> вже підключено.',
                    reply_markup=kb_manage_channel_inline, parse_mode='html')


async def save_cat_json(cat_name, message: types.Message):
    with open('data.json', 'r', encoding='utf-8') as file:
        file_data = json.load(file)

    # Створення нового словника cat_name
    file_data['catalogs'][cat_name] = {"videos": [],
                                       "photos": [],
                                       "voices": [],
                                       "documents": [],
                                       'gifs': [],
                                       'video_notes': [],
                                       'texts': []
                                       }
    # Записуємо оновлені дані назад у файл
    with open('data.json', 'w', encoding='utf-8') as file:
        json.dump(file_data, file, ensure_ascii=False, indent=4)


def cat_name_exist(cat_name):
    with open('data.json', 'r+', encoding='utf-8') as file:
        file_data = json.load(file)
        if cat_name not in file_data['catalogs']:
            return False
        else:
            return True


def catalog_list_json():
    with open('data.json', 'r+', encoding='utf-8') as file:
        file_data = json.load(file)
        catalogs = file_data['catalogs']
        return catalogs


def get_all_users_str() -> str:
    with open('data.json', 'r', encoding='utf-8') as file:
        file_data = json.load(file)
        users = "\n".join(
            [f"{name} - `{id}`" for id, name in file_data['users'].items()])
        return users


def get_all_channels(user_id):
    with open('data.json', 'r', encoding='utf-8') as file:
        file_data = json.load(file)
        return file_data['channels'].get(str(user_id))


async def remove_channel_id_from_json(channel_id, message: types.Message):
    with open('data.json', 'r', encoding='utf-8') as file:
        file_data = json.load(file)
    user_id = str(message.from_user.id)
    if channel_id in file_data['channels'][user_id]:
        channel_name = file_data['channels'][user_id][channel_id]
        del file_data['channels'][user_id][channel_id]

        with open('data.json', 'w', encoding='utf-8') as file:
            json.dump(file_data, file, indent=4, ensure_ascii=False)

        await message.answer(text=f'Ви відключили канал: {channel_name}', reply_markup=kb_manage_channel_inline)
    else:
        await message.answer(text=f'Каналу з таким id не існує', reply_markup=kb_manage_channel_inline)


async def add_media_to_catalog(messages: List[types.Message], bot, catalog_name):
    from utils import send_voice_from_audio
    photos, gifs, voices, documents, videos, video_notes, texts = [], [], [], [], [], [], []
    for message in messages:
        if message.content_type == 'photo':
            photos.append(message.photo[0].file_id)
        elif message.content_type == 'video':
            videos.append(message.video.file_id)
        elif message.content_type == 'animation':
            gifs.append(message.animation.file_id)
        elif message.content_type in ('voice', 'audio', 'video_note'):
            if message.content_type == 'voice':
                voices.append(message.voice.file_id)
            elif message.content_type == 'audio':
                await message.answer(text='Переформатування аудіо у голосове...')
                voice_message = await send_voice_from_audio(message=messages[0], bot=bot)
                voices.append(voice_message.voice.file_id)
            elif message.content_type == 'video_note':
                video_notes.append(message.video_note.file_id)
        elif message.content_type == 'document':
            documents.append(message.document.file_id)
        elif message.content_type == 'text':
            texts.append(message.text)

    with open('data.json', 'r+', encoding='utf-8') as file:
        file_data = json.load(file)
        file_data['catalogs'][catalog_name]["photos"].extend(photos)
        file_data['catalogs'][catalog_name]["videos"].extend(videos)
        file_data['catalogs'][catalog_name]["voices"].extend(voices)
        file_data['catalogs'][catalog_name]["documents"].extend(documents)
        file_data['catalogs'][catalog_name]["gifs"].extend(gifs)
        file_data['catalogs'][catalog_name]["video_notes"].extend(video_notes)
        if file_data['catalogs'][catalog_name].get("texts"):
            file_data['catalogs'][catalog_name]["texts"].extend(texts)
        else:
            file_data['catalogs'][catalog_name]["texts"] = texts
        file.seek(0)
        json.dump(file_data, file, ensure_ascii=False, indent=4)


async def get_catalog(cat_name):
    with open('data.json', 'r', encoding='utf-8') as file:
        file_data = json.load(file)
        catalog = file_data['catalogs'][cat_name]
        catalog = {k: v for k, v in catalog.items() if v}
        return catalog


def remove_cat_media_json(cat_name, media_type, media_indexes):
    with open('data.json', 'r+', encoding='utf-8') as file:
        file_data = json.load(file)
        print(media_indexes[::-1])
        for index in media_indexes[::-1]:
            del file_data['catalogs'][cat_name][media_type][index]

        file.seek(0)
        json.dump(file_data, file, ensure_ascii=False, indent=4)
        file.truncate()


def delete_catalog_json(cat_name):
    with open('data.json', 'r+', encoding='utf-8') as file:
        file_data = json.load(file)
        del file_data['catalogs'][cat_name]
        file.seek(0)
        json.dump(file_data, file, ensure_ascii=False, indent=4)
        file.truncate()


async def get_media_from_base(message: types.Message, cat_name, media_type, media_indexes: list):
    with open('data.json', 'r', encoding='utf-8') as file:
        file_data = json.load(file)
        res = []
        try:
            if max(media_indexes) + 1 <= len(file_data['catalogs'][cat_name][media_type]):
                for media_index in media_indexes:
                    file_id = file_data['catalogs'][cat_name][media_type][media_index]
                    res.append(CustomMessage(file_id=file_id, media_type=media_type, message=message))
                return res
            else:
                await message.answer(text='Введіть допустимі значення')
                return
        except:
            await message.answer(text='Введіть допустимі значення')
            return


def get_video_notes_by_cat(cat_name):
    with open('data.json', 'r', encoding='utf-8') as file:
        file_data = json.load(file)
        catalog_data = file_data.get('catalogs').get(cat_name)
        video_notes = catalog_data.get('video_notes')
        if len(video_notes) > 1:
            return video_notes
        else:
            return False


def change_cat_name(cat_name, new_name):
    with open('data.json', 'r+', encoding='utf-8') as file:
        file_data = json.load(file)
        file_data['catalogs'][new_name] = file_data['catalogs'].pop(cat_name)
        file.seek(0)
        json.dump(file_data, file, ensure_ascii=False, indent=4)
        file.truncate()


def get_texts_from_cat(cat_name):
    with open('data.json', 'r', encoding='utf-8') as file:
        file_data = json.load(file)
        catalog_data = file_data.get('catalogs').get(cat_name)
        texts = catalog_data.get('texts')
        return texts


class CustomMessage:
    def __init__(self, file_id, media_type, message: types.Message):
        self.file_id = file_id
        self.media_type = media_type
        self.message = message

    @property
    def content_type(self):
        return self.media_type

    async def answer(self, text, reply_markup=None):
        await self.message.answer(text=text, reply_markup=reply_markup)
