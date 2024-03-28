from datetime import datetime

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, BotCommand

kb_manage_channel_inline = InlineKeyboardMarkup(row_width=2)

add_channel_inline = InlineKeyboardButton(text='Додати канал', callback_data='Додати канал')
del_channel = InlineKeyboardButton(text='❌ Видалити канал', callback_data='Видалити канал')
channel_list = InlineKeyboardButton(text='Список каналів', callback_data='Список каналів')

kb_manage_channel_inline.add(add_channel_inline, del_channel, channel_list)

main_kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
channel_menu = KeyboardButton(text='Канали')
create_post = KeyboardButton(text='Створити пост')
edit_post = KeyboardButton(text='Змінити пост')
media_base = KeyboardButton(text='База даних')
signals = KeyboardButton(text='📣 Сигнали')
my_posts = KeyboardButton(text='Мої пости')
main_kb.add(create_post, channel_menu, edit_post, media_base, my_posts, signals)

cancel_kb = InlineKeyboardMarkup()
cancel = InlineKeyboardButton(text='Відміна', callback_data='Відміна')
cancel_kb.add(cancel)

cancel_sending_media_kb = InlineKeyboardMarkup()
cancel_media = InlineKeyboardButton(text='Відміна', callback_data='cancel_media')
cancel_sending_media_kb.add(cancel_media)

post_formatting_kb = InlineKeyboardMarkup(row_width=2)
plan_menu = InlineKeyboardButton(text='🗓 Планування', callback_data='Планування')
change_text = InlineKeyboardButton(text='📝 Змінити текст', callback_data='Змінити текст')
del_post_inline = InlineKeyboardButton(text='❌ Видалити пост', callback_data='delete_post')
inlines = InlineKeyboardButton(text='Інлайни', callback_data='inlines')
media_settings = InlineKeyboardButton(text='🎞 Налаштувати медіа', callback_data='Налаштувати медіа')
reset_post = InlineKeyboardButton(text='❌ Скинути пост', callback_data='reset_post')
post_now = InlineKeyboardButton(text='Опублікувати зараз 🚀', callback_data='Опублікувати')

post_formatting_kb.add(plan_menu, media_settings, change_text, inlines, reset_post, post_now)

back_to_plan_menu = InlineKeyboardButton(text='« Назад', callback_data='Планування')
back_to_formatting = InlineKeyboardButton(text='« Назад', callback_data='formatting_main_menu')
make_plan = InlineKeyboardButton(text='🗓 Запланувати', callback_data='Запланувати')
post_loop = InlineKeyboardButton(text='🌀 Зациклити', callback_data='Зациклити')
plan_menu_kb = InlineKeyboardMarkup(row_width=2)
plan_menu_kb.add(make_plan, post_loop, back_to_formatting)

back_to_media_settings = InlineKeyboardButton(text='« Назад', callback_data='Налаштувати медіа')
back_to_catalog = InlineKeyboardButton('« Назад', callback_data='back_to_catalog')

inlines_menu_kb = InlineKeyboardMarkup(row_width=2)
add_inline = InlineKeyboardButton(text='Додати інлайн', callback_data='add_inline')
del_inline = InlineKeyboardButton(text='Видалити інлайн', callback_data='del_inline')
edit_inline_link = InlineKeyboardButton(text='Змінити посилання', callback_data='edit_inline_link')
back_to_inlines = InlineKeyboardButton(text='« Назад', callback_data='inlines')
inlines_menu_kb.add(add_inline, edit_inline_link, back_to_formatting, del_inline)

back = InlineKeyboardButton(text='« Назад', callback_data='back')
back_to_main_menu = InlineKeyboardButton(text='« Назад', callback_data='main_menu')

back_edit_post_inline = InlineKeyboardButton(text='« Назад', callback_data='Змінити пост')

create_post_inline_kb = InlineKeyboardMarkup(row_width=2)
create_post_inline = InlineKeyboardButton(text='Створити пост', callback_data='Створити пост')
create_post_inline_kb.add(create_post_inline, back_edit_post_inline)

media_choice_kb = InlineKeyboardMarkup(row_width=2)
take_from_db = InlineKeyboardButton(text='Обрати з бази', callback_data='take_from_db')
send_by_self = InlineKeyboardButton(text='Додати самостійно', callback_data='send_by_self')
remove_media = InlineKeyboardButton(text='❌ Видалити медіа', callback_data='remove_media')
media_choice_kb.add(take_from_db, send_by_self, remove_media)

back_kb = InlineKeyboardMarkup()
back_kb.add(back)

base_manage_panel_kb = InlineKeyboardMarkup(row_width=2)
create_catalog = InlineKeyboardButton(text='Створити каталог', callback_data='Створити каталог')
edit_catalog = InlineKeyboardButton(text='Редагувати каталог', callback_data='edit_cat')
catalog_list_inline = InlineKeyboardButton(text='Оглянути каталоги', callback_data='cat_list')
delete_catalog_inline = InlineKeyboardButton(text='❌ Видалити каталог', callback_data='delete_cat')
base_manage_panel_kb.add(create_catalog, edit_catalog, catalog_list_inline, delete_catalog_inline)

add_to_cat_kb = InlineKeyboardMarkup(row_width=3)
add_video_img = InlineKeyboardButton(text='Відео/Фото/GIF', callback_data='Відео/Фото/GIF')
add_audio_voice = InlineKeyboardButton(text='Аудіо/Голосове', callback_data='Аудіо/Голосове')
add_file = InlineKeyboardButton(text='Файл', callback_data='Файл')
add_to_cat_kb.add(add_video_img, add_audio_voice, add_file)

enter_text_kb = InlineKeyboardMarkup(row_width=2)
pick_text_from_db = InlineKeyboardButton(text='Обрати з бази', callback_data='pick_text_from_db')
random_text = InlineKeyboardButton(text='Рандом текст', callback_data='random_text')
no_text_inline = InlineKeyboardButton(text='Без тексту', callback_data='no_text')
enter_text_kb.add(pick_text_from_db, random_text, no_text_inline)

del_voice_kb = InlineKeyboardMarkup()
del_voice_kb.add(InlineKeyboardButton(text='Так', callback_data='yes'))
del_voice_kb.add(InlineKeyboardButton(text='Ні', callback_data='no'))

edit_catalog_kb = InlineKeyboardMarkup(row_width=2)
edit_catalog_kb.add(InlineKeyboardButton(text='Додати медіа', callback_data='add_cat_media'),
                    InlineKeyboardButton(text='Змінити назву', callback_data='change_cat_name'),
                    InlineKeyboardButton(text='« Назад', callback_data='back_to_base_menu'),
                    InlineKeyboardButton(text='Видалити медіа', callback_data='del_cat_media'),

                    )

# remove_media_cat_type = InlineKeyboardMarkup()
video_type = InlineKeyboardButton(text='Відео', callback_data='videos')
photo_type = InlineKeyboardButton(text='Фото', callback_data='photos')
animation_type = InlineKeyboardButton(text='GIF', callback_data='gifs')
voice_type = InlineKeyboardButton(text='Голосове', callback_data='voices')
document_type = InlineKeyboardButton(text='Файл', callback_data='documents')
v_note_type = InlineKeyboardButton(text='Відеоповідомлення', callback_data='video_notes')
text_type = InlineKeyboardButton(text='Текст', callback_data='texts')

# planning_kb = InlineKeyboardMarkup(row_width=2)
# date_choose = InlineKeyboardButton(text='Обрати дату/час', callback_data='choose_date')
# planning_kb.add(back_to_formatting, date_choose)


change_post_kb = InlineKeyboardMarkup()
change_post = InlineKeyboardButton(text='Змінити пост', callback_data='Змінити пост')
change_post_kb.add(change_post)

change_create_post_kb = InlineKeyboardMarkup(row_width=2)
my_posts_inline = InlineKeyboardButton(text='Мої пости', callback_data='Мої пости')
change_create_post_kb.add(create_post_inline, change_post, my_posts_inline)

self_or_random_kb = InlineKeyboardMarkup(row_width=2)
random_inline = InlineKeyboardButton(text='🎞 Рандом медіа', callback_data='random_media')
random_videonote = InlineKeyboardButton(text='⭕️ Рандомм кругляши', callback_data='random_videonote')
self_media_inline = InlineKeyboardButton(text='Обрати самому', callback_data='self_media')
self_or_random_kb.add(random_videonote, random_inline, self_media_inline, back)

media_kb = InlineKeyboardMarkup(row_width=2)
media_kb.add(take_from_db, send_by_self, back_to_formatting, remove_media)

back_to_my_posts_inline = InlineKeyboardButton(text='« Назад', callback_data='Мої пости')

random_v_note_kb = InlineKeyboardMarkup()
save_added_v_notes = InlineKeyboardButton(text='💾 Зберегти', callback_data='save_added_v_notes')
back_to_media_variant = InlineKeyboardButton(text='Відміна', callback_data='back_to_media_variant')
random_v_note_kb.add(save_added_v_notes, back_to_media_variant)


def add_posts_to_kb(jobs, edit_kb):
    for j in jobs:
        date_p: datetime = j.next_run_time
        job_data = j.kwargs['data']
        skip_minutes_loop = job_data.get('skip_minutes_loop')
        if skip_minutes_loop:
            skip_minutes_loop = f" +{skip_minutes_loop}хв"
        else:
            skip_minutes_loop = ''
        if not job_data.get('post_text'):
            job_post_text = ''
        elif not job_data.get('post_text') and job_data.get('random_v_notes_id'):
            job_post_text = '- кругляш'
        else:
            job_post_text = f'- "{job_data.get("post_text")[:20]}"'
        if isinstance(job_post_text, list):
            job_post_text = job_post_text[0][:20]
        trigger_name = str(j.trigger).split('[')[0]
        if trigger_name == 'date':
            text = f"Пост {date_p.date()} о {date_p.strftime('%H:%M')}{skip_minutes_loop} {job_post_text}"
        elif trigger_name in ('interval', 'cron'):
            if trigger_name == 'interval':
                skip_days = job_data.get('skip_days_loop') if job_data.get(
                    'skip_days_loop') is not None else job_data.get('skip_days_loop_vnotes')
                start_loop_date = job_data.get('start_loop_date').strftime("%d.%m.%Y")
                skip_days = int(skip_days)
                if skip_days == 0:
                    text = f"🌀 з {start_loop_date} - о {date_p.strftime('%H:%M')}{skip_minutes_loop} {job_post_text}"
                elif skip_days == 1:
                    text = f"Початок {start_loop_date} - пропуск 1 день о {date_p.strftime('%H:%M')}{skip_minutes_loop} {job_post_text}"
                else:
                    text = f"Початок {start_loop_date} - пропуск {skip_days} дні(-в) о {date_p.strftime('%H:%M')}{skip_minutes_loop} {job_post_text}"
            else:
                text = f"🌀 {date_p.strftime('%H:%M')}{skip_minutes_loop} {job_post_text}"

        else:
            text = 'Без імені'

        edit_kb.add(InlineKeyboardButton(text=text,
                                         callback_data=j.id))


media_types = {"videos": video_type, "photos": photo_type, "gifs": animation_type, "voices": voice_type,
               "documents": document_type, 'video_notes': v_note_type, 'texts': text_type}


def cat_types_kb(cat_data_types):
    kb = InlineKeyboardMarkup()
    for data_type in cat_data_types:
        kb.add(media_types[data_type])
    return kb


def create_catalogs_kb(page=None):
    catalogs_kb = InlineKeyboardMarkup()
    from json_functionality import catalog_list_json
    catalogs: dict = catalog_list_json()
    catalog_by_page = list(catalogs)[page-1:30*page]
    for cat_name in catalog_by_page:
        catalogs_kb.add(InlineKeyboardButton(text=cat_name, callback_data=cat_name))
    return catalogs_kb
