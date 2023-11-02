from copy import deepcopy
from typing import List
from aiogram.utils.exceptions import BadRequest
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaVideo

from aiogram_media_group import media_group_handler
from create_bot import bot, scheduler
from json_functionality import add_media_to_catalog, catalog_list_json, cat_name_exist, save_cat_json, get_catalog, \
    get_media_from_base, remove_cat_media_json, delete_catalog_json, change_cat_name
from keyboards.kb_client import base_manage_panel_kb, back_kb, self_or_random_kb, post_formatting_kb, \
    change_create_post_kb, cat_types_kb, back, cancel_sending_media_kb, back_to_catalog, edit_catalog_kb, \
    create_catalogs_kb
from utils import pressed_back_button, cat_content, restrict_media, set_caption, show_post


async def media_base_panel(message, state: FSMContext):
    await state.finish()
    if isinstance(message, types.CallbackQuery):
        if message.data in ('back', 'back_to_base_menu'):
            await message.message.edit_text(text='Панель управління каталогами:',
                                            reply_markup=base_manage_panel_kb)
        else:
            await message.message.answer(text='Панель управління каталогами медіа', reply_markup=base_manage_panel_kb)

    else:
        await message.answer(text='Панель управління каталогами медіа', reply_markup=base_manage_panel_kb)


@media_group_handler
async def load_media_for_catalog(messages: List[types.Message], state: FSMContext):
    from handlers.client import FSMClient
    fsm_data = await state.get_data()
    kb = deepcopy(base_manage_panel_kb)
    if fsm_data.get('channel_id'):
        kb.add(InlineKeyboardButton(text='« Повернутись до поста', callback_data='formatting_main_menu'))
    if pressed_back_button(messages[0]):
        await state.reset_state(with_data=False)
        await media_base_panel(message=messages[0], state=state)
        return
    cat_name = fsm_data.get('cat_name')
    await add_media_to_catalog(messages, bot=bot, catalog_name=cat_name)
    await state.reset_state(with_data=False)
    await FSMClient.add_delete_cat_media.set()

    await messages[0].answer(text=f'Медіа додано у каталог "{cat_name}"', reply_markup=edit_catalog_kb)


async def catalog_list(call: types.CallbackQuery):
    from handlers.client import FSMClient
    await call.answer()
    catalogs = catalog_list_json()
    if catalogs:
        catalogs_kb = create_catalogs_kb()
        await FSMClient.show_catalog.set()
        await call.message.answer(text='Оберіть каталог, щоб подивитись зміст:', reply_markup=catalogs_kb)
    else:
        try:
            await call.message.edit_text(text='Немає жодного каталогу', reply_markup=base_manage_panel_kb)
        except:
            pass


async def create_cat(call: types.CallbackQuery):
    from handlers.client import FSMClient
    await FSMClient.create_cat_name.set()
    await call.message.edit_text(text='Введіть назву каталогу', reply_markup=back_kb)


async def load_cat_name(message, state: FSMContext):
    if pressed_back_button(message=message):
        await state.reset_state(with_data=False)
        await media_base_panel(message=message, state=state)
        return
    if cat_name_exist(cat_name=message.text):
        await message.answer(text='Такий каталог вже існує.\n'
                                  'Введіть іншу назву:')
    else:
        await save_cat_json(message.text, message=message)
        await state.update_data(cat_name=message.text)
        await message.answer(f'Каталог "{message.text}" створено.\n'
                             f'🎞 Надішліть або перешліть сюди медіа.\n'
                             'Можете також надіслати згруповані фото або відео:\n'
                             '\t<i>-фото;</i>\n'
                             '\t<i>-відео;</i>\n'
                             '\t<i>-голосове повідомлення;</i>\n'
                             '\t<i>-файл;</i>\n'
                             '\t<i>-текст</i>', parse_mode='html', reply_markup=back_kb)
        await state.reset_state(with_data=False)
        from handlers.client import FSMClient
        await FSMClient.loaded_catalog_file.set()


async def show_catalog_content(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    cat_name = call.data

    catalog_data = get_catalog(cat_name)

    if any(catalog_data.get(data) for data in catalog_data):
        await cat_content(call=call, catalog_data=catalog_data)
        await media_base_panel(message=call, state=state)
    else:
        await state.reset_state(with_data=False)
        try:
            await call.message.edit_text(text='Каталог пустий', reply_markup=base_manage_panel_kb)
        except:
            pass


async def edit_catalog_list(call: types.CallbackQuery, state: FSMContext):
    from handlers.client import FSMClient
    await call.answer()

    catalogs = catalog_list_json()

    if catalogs:
        catalogs_kb = create_catalogs_kb()
        catalogs_kb.add(InlineKeyboardButton(text='« Назад', callback_data='back_to_base_menu'))
        await FSMClient.edit_catalog.set()
        await call.message.edit_text(text='Оберіть каталог, який хочете редагувати: ', reply_markup=catalogs_kb)
    else:
        try:
            await call.message.edit_text(text='Немає жодного каталогу', reply_markup=base_manage_panel_kb)
        except:
            pass


async def choose_catalog(call: types.CallbackQuery, state: FSMContext):
    fsm_data = await state.get_data()
    post_type = fsm_data.get('post_type')
    await call.answer()
    if call.data == 'back':
        from handlers.client import choose_or_self_media
        await state.reset_state(with_data=False)
        await choose_or_self_media(call, state)
        return
    if call.data not in ('random_media', 'self_media', 'take_from_db', 'back_to_catalog'):
        await state.update_data(choose_catalog=call.data)
    from handlers.client import FSMClient

    if post_type == 'now':
        await media_type_from_cat(call, state)
    else:
        await FSMClient.random_or_self.set()
        try:
            await call.message.edit_text(
                text='Якщо хочете щоб медіа обирались для посту автоматично - оберіть "Рандом медіа".',
                reply_markup=self_or_random_kb)
        except:
            pass


async def media_type_from_cat(call: types.CallbackQuery, state: FSMContext):
    from handlers.client import FSMClient

    await call.answer()
    fsm_data = await state.get_data()
    cat_name = fsm_data.get('choose_catalog')
    if not cat_name:
        cat_name = call.data
    await state.update_data(catalog_for_post=cat_name)
    catalog_data = get_catalog(cat_name)
    catalog_data.pop('texts', None)


    if any(catalog_data.get(data) for data in catalog_data):
        catalog = get_catalog(cat_name)
        cat_data_types = [media_type for media_type in catalog if catalog.get(media_type)]
        kb = cat_types_kb(cat_data_types)
        kb.add(back_to_catalog)
        try:
            await call.message.edit_text(text='Що саме хочете додати?', reply_markup=kb)
        except:
            pass
        await FSMClient.media_type_add_from_cat.set()
    else:
        try:
            catalogs = catalog_list_json()
            if catalogs:
                catalogs_kb = create_catalogs_kb()
                catalogs_kb.add(back)
                await FSMClient.choose_catalog.set()
            await call.message.edit_text(text='У каталозі немає медіа.', reply_markup=catalogs_kb)
        except:
            pass


async def choose_media_from_cat(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    if call.data == 'back_to_catalog':
        await choose_catalog(call, state)
        return
    fsm_data = await state.get_data()
    post_type = fsm_data.get('post_type')
    if post_type in ('planned', 'looped', 'now') and call.data == 'back':
        from handlers.client import number_of_random_photos
        await number_of_random_photos(call, state)
        return
    cat_name = fsm_data.get('catalog_for_post')
    if not cat_name:
        cat_name = fsm_data.get('choose_catalog')

    catalog_data = get_catalog(cat_name)
    await state.update_data(media_type_add_from_cat=call.data)
    await cat_content(call=call, catalog_data=catalog_data, media_type=call.data)

    await call.message.answer(
        text='Надішліть номер медіа(або кілька номерів через пробіл), які бажаєте додати до посту:',
        reply_markup=cancel_sending_media_kb)

    from handlers.client import FSMClient
    await FSMClient.add_media_from_cat.set()


async def add_media_from_catalog(message: types.Message, state: FSMContext):
    data = await state.get_data()
    post_text = data.get('post_text')
    media_type = data.get('media_type_add_from_cat')
    cat_name = data.get('catalog_for_post')
    job_id = data.get('job_id')
    kb_inline = data.get('inline_kb')

    # if job_id то дані будуть з джоба
    if job_id:
        job = scheduler.get_job(job_id)
        data = scheduler.get_job(job_id).kwargs.get('data')
    if isinstance(message, types.CallbackQuery):
        if message.data == 'cancel_media':
            await media_type_from_cat(message, state)
            return

    elif isinstance(message, types.Message):
        media_indexes = [int(x) - 1 for x in message.text.split(' ') if x.isdigit()]
        messages = await get_media_from_base(message, cat_name, media_type, media_indexes)
        media = data.get('loaded_post_files')
        if not media:
            media = types.MediaGroup()
        if not messages:
            return
        if await restrict_media(messages=messages, state=state, data=data, post_formatting_kb=post_formatting_kb):
            return
        if media_type == 'voices':
            if job_id:
                data['voice'] = messages[0].file_id
                job.modify(kwargs={'data': data})
            else:
                await state.update_data(voice=messages[0].file_id)

            await message.answer_voice(voice=messages[0].file_id, reply_markup=kb_inline)
            await message.answer(text='✅ Голосове додано до посту.', reply_markup=post_formatting_kb)
            await state.reset_state(with_data=False)
            return
        elif media_type == 'video_notes':
            if job_id:
                data['video_note'] = messages[0].file_id
                job.modify(kwargs={'data': data})
            else:
                await state.update_data(video_note=messages[0].file_id)
            await message.answer_video_note(video_note=messages[0].file_id, reply_markup=kb_inline)
            await message.answer(text='✅ Відеоповідомлення додано до посту.', reply_markup=post_formatting_kb)
            await state.reset_state(with_data=False)
            return

        if media_type == 'videos':
            for video in messages:
                media.attach_video(video=video.file_id)
        elif media_type == 'photos':
            for photo in messages:
                media.attach_photo(photo=photo.file_id)
        elif media_type == 'documents':
            for document in messages:
                media.attach_document(document=document.file_id)
        set_caption(media=media, text=post_text)
        if job_id:
            data['loaded_post_files'] = media
            job.modify(kwargs={'data': data})
        else:
            await state.update_data(loaded_post_files=media)
        try:
            await show_post(message, state)
        except BadRequest:
            await message.answer(text='❌ Цей тип медіа не може бути згрупований з попередніми медіа.')
            media.media.pop()

        if job_id:
            await message.answer(text='✅ Медіа змінено.', reply_markup=change_create_post_kb)
        else:
            await message.answer(text='✅ Медіа додано.\n'
                                      'Оберіть варіант:', reply_markup=post_formatting_kb)
    await state.reset_state(with_data=False)


async def what_to_edit_cat(call: types.CallbackQuery, state: FSMContext):
    from handlers.client import FSMClient
    await call.answer()

    message_data = call.data
    if message_data == 'back_to_base_menu':
        await media_base_panel(call, state)
        return
    await state.update_data(cat_name=message_data)
    await FSMClient.add_delete_cat_media.set()
    try:
        await call.message.edit_text(text='Що бажаєте змінити?', reply_markup=edit_catalog_kb)
    except:
        pass


async def edit_cat(call: types.CallbackQuery, state: FSMContext):
    from handlers.client import FSMClient
    await call.answer()
    message_data = call.data
    fsm_data = await state.get_data()
    cat_name = fsm_data.get('cat_name')

    if message_data == 'add_cat_media':
        await call.message.answer(f'🎞 Надішліть або перешліть сюди медіа.\n'
                                  'Можете також надіслати згруповані фото або відео:\n'
                                  '\t<i>-фото;</i>\n'
                                  '\t<i>-відео;</i>\n'
                                  '\t<i>-голосове повідомлення;</i>\n'
                                  '\t<i>-відеоповідомлення;</i>\n'
                                  '\t<i>-файл;</i>', parse_mode='html', reply_markup=back_kb)
        await state.reset_state(with_data=False)
        await FSMClient.loaded_catalog_file.set()
    elif message_data == 'del_cat_media':
        catalog_data = get_catalog(cat_name)

        if any(catalog_data.get(data) for data in catalog_data):
            catalog = get_catalog(cat_name)
            print(catalog)
            cat_data_types = [media_type for media_type in catalog if catalog.get(media_type)]
            kb = cat_types_kb(cat_data_types)
            await call.message.edit_text(text='Що бажаєте видалити?', reply_markup=kb)

            await FSMClient.catalog_media_type_remove.set()
        else:
            await state.reset_state(with_data=False)
            try:
                await call.message.edit_text(text='Каталог пустий', reply_markup=base_manage_panel_kb)
            except:
                pass
    elif message_data == 'change_cat_name':
        await call.message.edit_text(text='Введіть нову назву каталогу:', reply_markup=InlineKeyboardMarkup().add(back))
        await FSMClient.new_cat_name.set()
    elif message_data == 'back_to_base_menu':
        await media_base_panel(call, state)
        return


async def load_new_cat_name(message, state: FSMContext):
    fsm_data = await state.get_data()
    cat_name = fsm_data.get('cat_name')
    from handlers.client import FSMClient
    if isinstance(message, types.Message):
        new_name = message.text
        change_cat_name(cat_name=cat_name, new_name=new_name)
        await state.update_data(cat_name=new_name)
        await message.answer(text=f'✅ Назву каталога змінено на {new_name}', reply_markup=edit_catalog_kb)
        await FSMClient.add_delete_cat_media.set()

    else:
        await FSMClient.add_delete_cat_media.set()

        try:
            await message.message.edit_text(text='Що бажаєте змінити?', reply_markup=edit_catalog_kb)
        except:
            pass


async def catalog_remove_media_numder(call: types.CallbackQuery, state: FSMContext):
    from handlers.client import FSMClient
    await call.answer()
    fsm_data = await state.get_data()
    cat_name = fsm_data.get('cat_name')

    catalog_data = get_catalog(cat_name)
    await state.update_data(catalog_media_type_remove=call.data)
    await cat_content(call=call, catalog_data=catalog_data, media_type=call.data)

    await call.message.answer(text='Надішліть номер медіа, яке бажаєте видалити:')

    await FSMClient.del_cat_media_number.set()


async def remove_cat_media_by_number(message: types.Message, state: FSMContext):
    fsm_data = await state.get_data()
    cat_name = fsm_data.get('cat_name')
    media_type = fsm_data.get('catalog_media_type_remove')
    media_index = int(message.text) - 1
    try:
        remove_cat_media_json(cat_name, media_type, media_index)
        await message.answer(text='Медіа видалено', reply_markup=base_manage_panel_kb)
        await state.reset_state(with_data=False)
    except IndexError:
        await message.answer(text='Введіть коректний номер:')


async def delete_catalog_list(call: types.CallbackQuery):
    await call.answer()
    catalogs = catalog_list_json()
    if catalogs:
        catalogs_kb = create_catalogs_kb()
        await call.message.edit_text(text='🗑 Оберіть каталог, який хочете видалити:\n'
                                          '<i>Всі медіа у каталозі буде видалено.</i>', parse_mode='html',
                                     reply_markup=catalogs_kb)
        from handlers.client import FSMClient
        await FSMClient.del_catalog.set()
    else:
        try:
            await call.message.edit_text(text='Немає жодного каталогу.', reply_markup=base_manage_panel_kb)
        except:
            pass


async def delete_catalog(call: types.CallbackQuery, state: FSMContext):
    cat_name = call.data
    delete_catalog_json(cat_name=cat_name)
    await call.message.edit_text(text=f'Каталог {cat_name} видалено.', reply_markup=base_manage_panel_kb)
    await state.reset_state(with_data=False)


def register_handlers_catalog(dp: Dispatcher):
    from handlers.client import FSMClient
    # dp.register_message_handler(media_base_panel, Text(equals='База медіа'), state='*')
    dp.register_callback_query_handler(edit_cat, state=FSMClient.add_delete_cat_media)
    dp.register_callback_query_handler(catalog_remove_media_numder, state=FSMClient.catalog_media_type_remove)
    dp.register_callback_query_handler(delete_catalog_list, Text(equals='delete_cat'))
    dp.register_callback_query_handler(delete_catalog, state=FSMClient.del_catalog)
    dp.register_message_handler(remove_cat_media_by_number, state=FSMClient.del_cat_media_number)
    dp.register_callback_query_handler(media_type_from_cat, state=FSMClient.catalog_for_post)
    dp.register_callback_query_handler(choose_media_from_cat, state=FSMClient.media_type_add_from_cat)
    dp.register_message_handler(add_media_from_catalog, state=FSMClient.add_media_from_cat)
    dp.register_callback_query_handler(add_media_from_catalog, state=FSMClient.add_media_from_cat)
    dp.register_callback_query_handler(choose_catalog, state=FSMClient.choose_catalog)
    dp.register_callback_query_handler(create_cat, Text(equals='Створити каталог'))
    dp.register_callback_query_handler(catalog_list, Text(equals='cat_list'))
    dp.register_message_handler(load_cat_name, state=FSMClient.create_cat_name)
    dp.register_callback_query_handler(load_cat_name, state=FSMClient.create_cat_name)
    dp.register_message_handler(load_media_for_catalog, state=FSMClient.loaded_catalog_file,
                                content_types=types.ContentType.all())
    dp.register_callback_query_handler(load_media_for_catalog, state=FSMClient.loaded_catalog_file)
    dp.register_callback_query_handler(show_catalog_content, state=FSMClient.show_catalog)
    dp.register_callback_query_handler(edit_catalog_list, Text(equals='edit_cat'))
    dp.register_callback_query_handler(what_to_edit_cat, state=FSMClient.edit_catalog)
    dp.register_message_handler(load_new_cat_name, state=FSMClient.new_cat_name)
    dp.register_callback_query_handler(load_new_cat_name, state=FSMClient.new_cat_name)
