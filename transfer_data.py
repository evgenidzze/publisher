import asyncio
import json

from sqlalchemy import select

from db_manage import async_session, Catalog, Media, Channel


async def save_cat_media():
    async with async_session() as session:
        query = select(Catalog)
        res = await session.execute(query)
        catalogs = res.scalars().all()
        catalog_name_id = {catalog.name: catalog.id for catalog in catalogs}
    entries = []
    with open('data.json', 'r+', encoding='utf-8') as file:
        file_data = json.load(file)
        catalogs = file_data.get('catalogs')
        for catalog in catalogs:
            cat_data = catalogs.get(catalog)
            for key, value in cat_data.items():
                key = key[:-1]
                for v in value:
                    if key == 'text':
                        entries.append(Media(catalog_id=catalog_name_id[catalog], media_type='text', text=v))
                    else:
                        entries.append(Media(catalog_id=catalog_name_id[catalog], media_type=key, file_id=v))

    async with async_session() as session:
        session.add_all(entries)
        await session.commit()


async def save_channels():
    entries = []
    with open('data.json', 'r+', encoding='utf-8') as file:
        file_data = json.load(file)
        channels = file_data.get('channels')
        for user_id, value in channels.items():
            for channel_id, channel_name in value.items():
                entries.append(Channel(channel_id=channel_id, name=channel_name, owner_id=user_id))
    async with async_session() as session:
        session.add_all(entries)
        await session.commit()
