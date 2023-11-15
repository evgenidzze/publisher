from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

signal_locations_kb = InlineKeyboardMarkup(row_width=2)
uz_location = InlineKeyboardButton('🇺🇿 Узбекистан', callback_data='uz')
br_location = InlineKeyboardButton('🇧🇷 Бразилія', callback_data='br')
my_signals = InlineKeyboardButton(text='Встановлені сигнали', callback_data='my_signal_groups')
signal_locations_kb.add(uz_location, br_location, my_signals)

back_to_location = InlineKeyboardButton(text='« Назад', callback_data='📣 Сигнали')


signal_menu_kb = InlineKeyboardMarkup(row_width=2)
create_signal = InlineKeyboardButton(text='➕ Створити групу', callback_data='create_signal_group')
delete_signal = InlineKeyboardButton(text='❌ Видалити групу', callback_data='delete_signal_group')
signal_menu_kb.add(create_signal, delete_signal, back_to_location)

back_to_signal_panel_inline = InlineKeyboardButton(text='« Назад', callback_data='signal_panel')
back_to_choose_channel_inline = InlineKeyboardButton(text='« Назад', callback_data='create_signal_group')
back_to_enter_bet_inline = InlineKeyboardButton(text='« Назад', callback_data='enter_bet')
back_to_enter_coef_inline = InlineKeyboardButton(text='« Назад', callback_data='enter_coef')
back_enter_signal_count_inline = InlineKeyboardButton(text='« Назад', callback_data='enter_signal_count')
