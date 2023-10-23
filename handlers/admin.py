from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup

from config import ADMINS
from create_bot import bot
from json_functionality import save_user_id_to_json, remove_user_id_from_json, get_all_users_str
from keyboards.kb_admin import kb_manage_user, back_main_moder_menu_kb


class FSMAdmin(StatesGroup):
    user_id = State()
    remove_user_id = State()


async def moderator_start(message: types.Message, state: FSMContext):
    await state.finish()
    if isinstance(message, types.Message):
        if str(message.from_user.id) in ADMINS:
            await message.answer(text='Вітаю, адміністратор!', reply_markup=kb_manage_user)
        else:
            await message.answer(text='У вас немає прав модератора.')
    elif isinstance(message, types.CallbackQuery):
        await message.answer()
        if str(message.from_user.id) in ADMINS:
            await message.message.edit_text(text='Вітаю, адміністратор!', reply_markup=kb_manage_user)
        else:
            await message.message.edit_text(text='У вас немає прав модератора.')


async def manage_menu(message: types.Message):
    if isinstance(message, types.CallbackQuery):
        await message.answer()
    if str(message.from_user.id) in ADMINS:
        await bot.send_message(chat_id=message.from_user.id, text="Панель управління користувачами",
                               reply_markup=kb_manage_user)


async def add_user(message: types.CallbackQuery):
    if isinstance(message, types.CallbackQuery):
        await message.answer()
    if str(message.from_user.id) in ADMINS:
        await message.message.edit_text(text='Перешліть будь-яке повідомлення користувача.',
                                        reply_markup=back_main_moder_menu_kb)

        await FSMAdmin.user_id.set()


async def load_id(message: types.Message, state: FSMContext):
    if isinstance(message, types.CallbackQuery):
        await message.answer()
    if str(message.from_user.id) in ADMINS:
        if message.forward_from:
            await save_user_id_to_json(str(message.forward_from.id), message=message)
        elif message.forward_sender_name:
            await bot.send_message(chat_id=message.from_user.id, text='У користувача прихований id')
        else:
            await bot.send_message(chat_id=message.from_user.id, text='Невірний формат')
        await state.finish()


# Скасувати працівнику права
async def deny_user_access(message, state: FSMContext):
    await state.reset_state(with_data=False)
    if isinstance(message, types.CallbackQuery):
        await message.answer()
    if str(message.from_user.id) in ADMINS:
        await FSMAdmin.remove_user_id.set()
        all_users = get_all_users_str()
        try:
            await message.message.edit_text(text=f'Надішліть id користувача, якому хочете скасувати права.\n\n'
                                                 f'{all_users}', reply_markup=kb_manage_user, parse_mode="Markdown")
        except:
            pass


async def remove_id(message: types.Message, state: FSMContext):
    if isinstance(message, types.CallbackQuery):
        await message.answer()
    if str(message.from_user.id) in ADMINS:
        user_id = message.text
        if user_id.isdigit():
            await remove_user_id_from_json(user_id, message)
            await state.finish()
        else:
            await message.answer('id має складатись тільки з цифр, надішліть ще раз.')


async def user_list(call: types.CallbackQuery):
    if isinstance(call, types.CallbackQuery):
        await call.answer()
    if str(call.from_user.id) in ADMINS:
        try:
            await call.message.edit_text(text=get_all_users_str(), parse_mode="Markdown", reply_markup=kb_manage_user)
        except:
            pass


async def cancel_handler(message: types.Message, state: FSMContext):
    if isinstance(message, types.CallbackQuery):
        await message.answer()
    if str(message.from_user.id) in ADMINS:
        current_state = await state.get_state()
        if current_state is None:
            await message.answer('OK')
            return
        await state.finish()
        await message.answer('OK')
    else:
        await message.answer('У вас немає прав адміністратора')


def register_handlers_admin(dp: Dispatcher):
    dp.register_message_handler(moderator_start, commands=['moderator'], state='*')
    dp.register_callback_query_handler(moderator_start, Text(equals='moderator'), state='*')
    dp.register_message_handler(cancel_handler, Text(equals='Відміна', ignore_case=True), state="*")
    dp.register_callback_query_handler(cancel_handler, Text(equals='Відміна', ignore_case=True), state="*")
    #
    dp.register_message_handler(manage_menu, Text(equals='Користувачі'), state="*")

    dp.register_callback_query_handler(user_list, Text(equals='Список користувачів'), state="*")

    dp.register_callback_query_handler(add_user, Text(equals='Додати користувача'), state="*")
    dp.register_message_handler(load_id, state=FSMAdmin.user_id)

    dp.register_callback_query_handler(deny_user_access, Text(equals='Видалити користувача'), state="*")
    dp.register_message_handler(remove_id, state=FSMAdmin.remove_user_id)
