from typing import List

from aiogram import types
from sqlalchemy import select, insert, delete, exists, update, and_

from db_manage import User, async_session, Catalog, Media, Channel
from keyboards.kb_admin import kb_manage_user
from keyboards.kb_client import kb_manage_channel_inline


async def get_user(user_id) -> User:
    async with async_session() as session:
        stmt = select(User).where(User.telegram_id == user_id)
        res = await session.execute(stmt)
        user = res.fetchone()
        if user:
            return user[0]


async def save_user(user_id: str, message: types.Message):
    async with async_session() as session:
        user = await get_user(user_id)
        if user:
            await message.answer(text=f'У користувача з id: {user_id} вже є доступ.', reply_markup=kb_manage_user)
        else:
            query = insert(User).values(telegram_id=user_id, username=message.forward_from.username)
            await message.answer(text=f'Ви надали доступ користувачу {message.forward_from.username} з id: {user_id}',
                                 reply_markup=kb_manage_user)
        await session.execute(query)
        await session.commit()


async def delete_user(user_id, message: types.Message):
    async with async_session() as session:
        user = await get_user(user_id)
        if user:
            stmt = delete(User).where(User.telegram_id == user_id)
            await session.execute(stmt)
            await session.commit()
            await message.answer(text=f'Ви скасували права користувачу з id: {user_id}', reply_markup=kb_manage_user)
        else:
            await message.answer(text=f'Користувача з таким id не існує', reply_markup=kb_manage_user)


async def save_channel_json(channel_id: str, message: types.Message):
    async with async_session() as session:
        channel_name = message.forward_from_chat.title
        query = select(Channel).where(and_(Channel.channel_id == channel_id, Channel.owner_id == message.from_user.id))
        result = await session.execute(query)
        channel = result.scalar()
        if not channel:
            insert_query = insert(Channel).values(
                channel_id=channel_id,
                name=channel_name,
                owner_id=message.from_user.id
            )
            await session.execute(insert_query)
            await session.commit()
            text = (f'Канал <a href="{await message.forward_from_chat.get_url()}">{message.forward_from_chat.title}'
                    f'</a> з id: <code>{channel_id}</code> успішно підключений')
        else:
            text = (f'Канал <a href="{await message.forward_from_chat.get_url()}">{message.forward_from_chat.title}'
                    f'</a> з id: <code>{channel_id}</code> вже підключено.')

        await message.answer(text=text, reply_markup=kb_manage_channel_inline, parse_mode='html')


async def save_cat(cat_name):
    async with async_session() as session:
        query = insert(Catalog).values(name=cat_name)
        await session.execute(query)
        await session.commit()


async def cat_name_exist(cat_name):
    async with async_session() as session:
        stmt = select(exists().where(Catalog.name == cat_name))
        res = await session.execute(stmt)
        return res.scalar()


async def catalog_list_db() -> Catalog:
    async with async_session() as session:
        stmt = select(Catalog)
        res = await session.execute(stmt)
        catalogs = res.scalars().all()
        return catalogs


async def get_all_users_str() -> [User]:
    async with async_session() as session:
        stmt = select(User)
        res = await session.execute(stmt)
        users = res.scalars().all()
        return users


async def get_all_channels(user_id):
    async with async_session() as session:
        stmt = select(Channel).where(Channel.owner_id == user_id)
        res = await session.execute(stmt)
        channels = res.scalars().all()
        return channels


async def remove_channel_id_from_json(channel_id, message: types.Message):
    async with async_session() as session:
        stmt = delete(Channel).where(and_(Channel.channel_id == channel_id, Channel.owner_id == message.from_user.id))
        result = await session.execute(stmt)
        await session.commit()
        rows_deleted = result.rowcount
        if rows_deleted:
            await message.answer(text=f'Ви відключили канал: {channel_id}', reply_markup=kb_manage_channel_inline)
        else:
            await message.answer(text=f'Каналу з таким id не існує', reply_markup=kb_manage_channel_inline)


async def add_media_to_catalog(messages: List[types.Message], bot, cat_id):
    media_entries = []
    async with async_session() as session:
        for message in messages:
            if message.content_type == 'text':
                media_entries.append(Media(catalog_id=cat_id, media_type=message.content_type, text=message.text))
            else:
                from utils.utils import get_media_id
                file_id = await get_media_id(message)
                media_entries.append(Media(catalog_id=cat_id, media_type=message.content_type, file_id=file_id))
        session.add_all(media_entries)
        await session.commit()


async def get_all_catalog_media(cat_id, with_text=False) -> [Media]:
    async with async_session() as session:
        if with_text:
            stmt = select(Media).where(Media.catalog_id == cat_id)
        else:
            stmt = select(Media).where(and_(Media.catalog_id == cat_id, Media.media_type != 'text'))
        res = await session.execute(stmt)
        catalog = res.scalars().all()
        return catalog


async def get_media_by_type(cat_id, media_type) -> List[Media]:
    async with async_session() as session:
        stmt = select(Media).where(and_(Media.catalog_id == cat_id, Media.media_type == media_type))
        res = await session.execute(stmt)
        catalog = res.scalars().all()
        return catalog


async def get_media_by_indexes(cat_id, media_indexes) -> List[Media]:
    async with async_session() as session:
        stmt = select(Media).where(and_(Media.catalog_id == cat_id, Media.id.in_(media_indexes)))
        res = await session.execute(stmt)
        catalog = res.scalars().all()
        return catalog


async def remove_cat_media_json(cat_name, media_indexes):
    async with async_session() as session:
        stmt = delete(Media).where(and_(Media.catalog_id == cat_name, Media.id.in_(media_indexes)))
        await session.execute(stmt)
        await session.commit()


async def delete_catalog_json(cat_id):
    async with async_session() as session:
        query = delete(Catalog).where(Catalog.id == cat_id)
        await session.execute(query)
        await session.commit()


async def get_video_notes_by_cat(cat_id):
    async with async_session() as session:
        stmt = select(Media).where(Media.catalog_id == cat_id)
        res = await session.execute(stmt)
        video_notes = res.scalars().all()
        if len(video_notes) > 1:
            return video_notes
        else:
            return False


async def change_cat_name(cat_id, new_name):
    async with async_session() as session:
        stmt = update(Catalog).where(Catalog.id == cat_id).values(name=new_name)
        await session.execute(stmt)
        await session.commit()


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
