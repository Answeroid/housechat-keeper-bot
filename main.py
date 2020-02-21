# -*- coding: utf-8 -*-
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, InputMediaPhoto, ChatAction
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler, Filters, run_async
from telegram.error import (TelegramError, Unauthorized, BadRequest, TimedOut, NetworkError)
import sys
import os
import time
import re
import matplotlib.pyplot as plt
import matplotlib as mpl
from datetime import datetime
from models import User, Show, Jubilee
from constants import help_msg, about_msg, building_msg, houses_arr, greeting_msg
from classes import filt_integers, filt_call_err, block_filter
from config import log, log_chat, log_msg
from functools import wraps

KEY = sys.argv[1]
ADMIN_ID = sys.argv[2]
print('key ...' + KEY[-6:] + ' successfully used')


def send_typing_action(func):
    """Sends typing action while processing func command."""

    @wraps(func)
    def command_func(*args, **kwargs):
        bot, update = args
        bot.send_chat_action(chat_id=update.effective_message.chat_id, action=ChatAction.UPLOAD_DOCUMENT)
        return func(bot, update, **kwargs)

    return command_func


def chosen_owns(update):
    user_id = update.effective_user.id
    try:
        user = User.select().where(User.user_id == user_id)[Show.get(user_id=user_id).owns or 0]
    except IndexError:
        user = User.select().where(User.user_id == user_id)[0]
    return user


def is_changed(update):
    log.info(log_msg(update))
    # check if user exist in DB (both tables). If not - create
    username = update.effective_user.username
    user_id = update.effective_user.id
    full_name = update.effective_user.full_name

    user, created = User.get_or_create(user_id=user_id)
    Show.get_or_create(user_id=update.effective_user.id)

    if not created:
        # check if user changed own name attributes. If so - update
        if user.username != username or user.full_name != full_name:
            for user in User.select().where(User.user_id == user_id):
                user.username = username
                user.full_name = full_name
                if user.updated:
                    user.updated = datetime.now().strftime('%y.%m.%d %H:%M:%S.%f')[:-4]
                user.save()
    else:
        user.username = update.effective_user.username
        user.full_name = full_name
        user.save()


def start_command(update, context):
    """handle /start command"""
    log.info(log_msg(update))
    is_changed(update)
    if update.callback_query:
        update.callback_query.answer()
    menu_kbd(update, context)


def help_command(update, _):
    """handle /help command"""
    log.info(log_msg(update))
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton('Меню',
                                                               callback_data='_menu')]])
    update.message.reply_text(text=help_msg,
                              parse_mode=ParseMode.HTML,
                              reply_markup=reply_markup)


def about_command(update, _):
    """handle /about command"""
    log.info(log_msg(update))
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton('Меню',
                                                               callback_data='_menu')]])
    update.message.reply_text(text=about_msg,
                              parse_mode=ParseMode.HTML,
                              disable_web_page_preview=True,
                              reply_markup=reply_markup)


def building(update, _):
    """CallbackQueryHandler. pattern ^building$"""
    log.info(log_msg(update))
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton('Меню',
                                                               callback_data='_menu')]])
    update.message.reply_text(text=building_msg,
                              parse_mode=ParseMode.HTML,
                              disable_web_page_preview=True,
                              reply_markup=reply_markup)
    update.callback_query.answer()


def new_neighbor_report(update, _, created_user):
    """Send message for users who enabled notifications"""
    # TODO: rework this func
    log.info(log_msg(update))
    # query for users who set notifications as _notify_house
    query_params = Show.select(Show.user_id).where(Show.notification_mode == '_notify_house')
    query_users = User.select(User.user_id).where(User.house == created_user.house)
    query = query_params & query_users
    # prevent telegram blocking spam
    for i, user in enumerate(query):
        if i % 29 == 0:
            time.sleep(1)
        try:
            update.message.reply_text(chat_id=user.user_id,
                                      parse_mode=ParseMode.HTML,
                                      text=f'Новий сосед\n{created_user.joined_str()}')
        except BadRequest as err:
            update.message.reply_text(chat_id=ADMIN_ID,
                                      text=f'failed to send notification for user {user.user_id} {err}',
                                      parse_mode=ParseMode.HTML)

    # query for users who set notifications as _notify_section    
    query_params = Show.select(Show.user_id).where(Show.notification_mode == '_notify_section')
    query_users = query_users.where(User.section == created_user.section)
    query = query_params & query_users
    for i, user in enumerate(query):
        if i % 29 == 0:
            time.sleep(1)
        try:
            update.message.reply_text(chat_id=user.user_id,
                                      parse_mode=ParseMode.HTML,
                                      text=f'Новий сосед\n{created_user.joined_str()}')
        except BadRequest as err:
            update.message.reply_text(chat_id=ADMIN_ID,
                                      text=f'failed to send notification '
                                           f'for user {user.user_id} {err}',
                                      parse_mode=ParseMode.HTML)


def user_created_report(update, _, created_user, text):
    """when created new, or updated user - send report-message for admins"""
    update.message.reply_text(chat_id=ADMIN_ID,
                              parse_mode=ParseMode.HTML,
                              text=f'{text} {created_user.user_created()}')
    try:
        # TODO: add correct try statement
        # bot.sendMessage(chat_id=986555, parse_mode=ParseMode.HTML, text=f'{text} {created_user.user_created()}')
        pass
    except BadRequest:
        pass


def menu_kbd(update, _):
    """show keyboard to choose: show neighbors or edit own info"""
    log.info(log_msg(update))
    if User.get(user_id=update.effective_user.id).house \
            and User.get(user_id=update.effective_user.id).section:
        keyboard = [[InlineKeyboardButton('Смотреть соседей 👫', callback_data='show')],
                    [InlineKeyboardButton('Изменить свои данные ✏️', callback_data='edit')],
                    [InlineKeyboardButton('Важная информация ℹ️', callback_data='building')],
                    [InlineKeyboardButton('Статистика бота 📊️', callback_data='statistics')],
                    [InlineKeyboardButton('Мой дом 🏠', callback_data='house_neighbors'),
                     InlineKeyboardButton('Мой подъезд 🔢', callback_data='section_neighbors')],
                    [InlineKeyboardButton('Оповещения 🔔', callback_data='notifications')]]
    else:
        keyboard = [[InlineKeyboardButton('Добавить свои данные 📝', callback_data='edit')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    # TODO: cover that unified reply into different func
    if update.callback_query is not None:
        update.callback_query.message.reply_text(text="Выберите:",
                                                 reply_markup=reply_markup,
                                                 parse_mode=ParseMode.HTML)
    else:
        update.message.reply_text(text="Выберите:",
                                  reply_markup=reply_markup,
                                  parse_mode=ParseMode.HTML)


def check_owns(update, context):
    """check how many records for user in db"""
    log.info(log_msg(update))
    if not len(User.select().where(User.user_id == update.effective_user.id)) > 1:
        if update.callback_query.data == 'house_neighbors':
            show_house(update, context)
            return
        elif update.callback_query.data == 'section_neighbors':
            show_section(update, context)
            return
        else:
            if not User.get(user_id=update.effective_user.id).house:
                text = 'В каком вы доме?'
                set_houses_kbd(update, context, text)
            else:
                text = 'Изменяем ваши данные:\n' + User.get(
                    user_id=update.effective_user.id).setting_str() + \
                       '\nВ каком вы доме?'
                set_houses_kbd(update, context, text)
    # if more than 1 records for user, call func for select
    else:
        select_owns(update, context)


def select_owns(update, _):
    """if user have more than 1 records in db, select which one to show/edit"""
    log.info(log_msg(update))
    if update.callback_query.data == 'house_neighbors':
        text = 'Соседи по какому дому?'
        view_edit = 'view_my_house'
    elif update.callback_query.data == 'section_neighbors':
        text = 'ПОдъезд какой из ваших квартир?'
        view_edit = 'view_my_secti'
    else:
        text = 'Какой адрес изменить?'
        view_edit = 'edit'
    keyboard = []
    user_owns = User.select().where(User.user_id == update.effective_user.id)
    for i, j in enumerate(user_owns):
        keyboard.append([InlineKeyboardButton(str(j.edit_btn_str()),
                                              callback_data='set_owns' + str(i) + view_edit)])
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.message.reply_text(text=text,
                                             reply_markup=reply_markup,
                                             parse_mode=ParseMode.HTML)
    update.callback_query.answer()


def owns_selected(update, context):
    """save params to db"""
    log.info(log_msg(update))
    view_edit = update.callback_query.data[-13:]
    owns = [s for s in list(update.callback_query.data) if s.isdigit()]
    owns = int(''.join(owns))
    user = Show.get(user_id=update.effective_user.id)
    user.owns = owns
    user.save()

    if view_edit == 'view_my_house':
        show_house(update, context)
    elif view_edit == 'view_my_secti':
        show_section(update, context)
    else:
        user = User.select().where(User.user_id == update.effective_user.id)[owns]
        text = 'Изменяем ваши данные:\n' + user.setting_str() + '\nВ каком вы доме?'
        set_houses_kbd(update, context, text)
    update.callback_query.answer()


def houses_kbd(update, _):
    """show keyboard to chose house to show"""
    # TODO: change building numbers to be correct
    log.info(log_msg(update))
    keyboard = [[InlineKeyboardButton('Дом 11', callback_data='p_h85'),
                 InlineKeyboardButton('Дом 13', callback_data='p_h87')],
                [InlineKeyboardButton('Дом 5', callback_data='p_h89')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.message.reply_text('Какой дом показать?',
                                             reply_markup=reply_markup)
    update.callback_query.answer()


def section_kbd(update, _):
    user_query = Show.get(user_id=update.effective_user.id)
    user_query.house = int(update.callback_query.data[-2:])
    user_query.save()

    keyboard = [[InlineKeyboardButton('Подъезд №1', callback_data='p_s1'),
                 InlineKeyboardButton('Подъезд №2', callback_data='p_s2')],
                [InlineKeyboardButton('Подъезд №3', callback_data='p_s3'),
                 InlineKeyboardButton('Подъезд №4', callback_data='p_s4')],
                [InlineKeyboardButton('Показать всех в доме?',
                                      callback_data='show_this_house')]]

    if user_query.house == 87:
        del keyboard[1:3]

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.message.reply_text('Какой подъезд показать?',
                                             reply_markup=reply_markup)
    update.callback_query.answer()


def save_params(update, context):
    """callbackQuery from section_kbd(). save params to db table"""
    log.info(log_msg(update))
    user_query = Show.get(user_id=update.effective_user.id)
    user_query.section = int(update.callback_query.data[3])
    user_query.save()
    some_section = True
    show_section(update, context, some_section)
    update.callback_query.answer()


def set_houses_kbd(update, _, text=''):
    """show keyboard to chose its own house"""
    # TODO: rework that func completely
    log.info(log_msg(update))
    if not User.get(user_id=update.effective_user.id).house:
        text = text
    elif len(User.select().where(User.user_id == update.effective_user.id)) > 1:
        text = text
    else:
        text = text
    keyboard = [[InlineKeyboardButton('Дом №11', callback_data='_h85')],
                [InlineKeyboardButton('Дом №13', callback_data='_h87')],
                [InlineKeyboardButton('Дом №5', callback_data='_h89')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.message.reply_text(text=text,
                                             reply_markup=reply_markup,
                                             parse_mode=ParseMode.HTML)
    update.callback_query.answer()


def set_section_kbd(update, _):
    user = chosen_owns(update)
    user.house = int(update.callback_query.data[-2:])
    user.save()

    keyboard = [[InlineKeyboardButton('Подъезд №1', callback_data='_s1')],
                [InlineKeyboardButton('Подъезд №2', callback_data='_s2')],
                [InlineKeyboardButton('Подъезд №3', callback_data='_s3')],
                [InlineKeyboardButton('Подъезд №4', callback_data='_s4')],
                [InlineKeyboardButton('Завершить редактирование',
                                      callback_data='_section_reject')]]

    if user.house == 87:
        del keyboard[1:3]

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.message.reply_text('В каком вы подъезде?',
                                             reply_markup=reply_markup)
    update.callback_query.answer()


def set_floor_kbd(update, _):
    """callbackQuery from set_section_kbd().
    Show keyboard to chose its own floor"""
    log.info(log_msg(update))
    user = chosen_owns(update)
    user.section = int(update.callback_query.data[2])
    user.save()

    floors = houses_arr['house_' + str(user.house)]['section_' + str(user.section)]
    # TODO: add proper floor count
    keyboard = []
    count_ = len(floors)
    while count_ > 0:
        floor = []
        for i in range(3):
            if count_ == 0:
                break
            floor.append(InlineKeyboardButton(str(floors[-count_]),
                                              callback_data='_f' + str(floors[-count_])))
            count_ -= 1
        keyboard.append(floor)

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.message.reply_text('На каком этаже?',
                                             reply_markup=reply_markup)
    update.callback_query.answer()


def set_apartment_kbd(update, _):
    """func show message with ask to tell its own apartment"""
    log.info(log_msg(update))
    update.callback_query.answer()
    floor = [s for s in list(update.callback_query.data) if s.isdigit()]
    floor = int(''.join(floor))

    user = chosen_owns(update)
    user.floor = floor
    user.save()

    user_mode = Show.get(user_id=update.effective_user.id)
    user_mode.msg_apart_mode = True
    user_mode.save()

    text = 'В какой квартире? \nНапишите номер в сообщении или нажмите кнопку ниже.'
    keyboard = [[InlineKeyboardButton('Не хочу указывать квартиру',
                                      callback_data='_apart_reject')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    # TODO: add proper return after flat was added
    update.callback_query.message.reply_text(text=text,
                                             reply_markup=reply_markup)


def msg_handler(update, _):
    """handle all text msg except other filters do"""
    msg = update.message.text
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton('Меню',
                                                               callback_data='_menu')]])
    update.message.reply_text(
        photo=open(os.path.join('img', 'maybe.jpg'), 'rb'),
        reply_markup=reply_markup,
        caption=f'Я еще не понимать человеческий. Лучше воспользуйтесь меню.')
    log.info(log_msg(update) + f' text: {msg}')


def group_chat_logging(update, _):
    """handle text msgs in group chat. MessageHandler((Filters.text & Filters.group)"""
    msg = update.message.text
    log_chat.info(log_msg(update) + f' msg: {msg}')


def jubilee(update, _, created_user):
    """Check if new added user is 'hero of the day' i.e some round number in db"""
    log.info(log_msg(update))
    celebration_count = [i for i in range(0, 2000, 50)]
    query = User.select().where(User.house, User.section)

    check_list = {85: query.where(User.house == 85).count(),
                  87: query.where(User.house == 87).count(),
                  89: query.where(User.house == 89).count()}
    total = query.count()
    text = f'Соседей 🎇 🎈 🎉 🎆 🍹\nПриветствуем!\n{created_user.joined_str()}'

    for house in check_list.items():
        if house[1] in celebration_count:
            x, created = Jubilee.get_or_create(house=house[0], count=house[1])
            if created:
                text = f'В доме № {house[0]} уже зарегистрировано {house[1]} ' + text
                try:
                    # TODO: rework Jubilee
                    continue
                    # update.message.reply_text(chat_id=-1001076439601, text=text, parse_mode=ParseMode.HTML)  # test chat
                except BadRequest:
                    continue
                    # update.message.reply_text(chat_id=-1001118126927, text=text, parse_mode=ParseMode.HTML)  # group chat

    if total in celebration_count:
        text = f'Уже зарегистрировано {total} соседей 🎇 🎈 🎉 🎆 🍹\nПриветствуем!\n{created_user.joined_str()}'
        x, created = Jubilee.get_or_create(house=0, count=total)
        if created:
            try:
                pass
                # update.message.reply_text(chat_id=-1001076439601, text=text, parse_mode=ParseMode.HTML)  # test chat
            except BadRequest:
                pass
                # update.message.reply_text(chat_id=-1001118126927, text=text, parse_mode=ParseMode.HTML)  # group chat


def apartment_save(update, context):
    """integer text handler"""
    log.info(log_msg(update))
    user_mode = Show.get(user_id=update.effective_user.id)
    if user_mode.msg_apart_mode:
        apartment = int(update.message.text)
        user = chosen_owns(update)
        user.apartment = apartment
        if not user.updated:
            text = 'В базу ДОБАВЛЕН:\n'
        else:
            text = 'В базе ОБНОВЛЕН:\n'
        user.updated = datetime.now().strftime('%y.%m.%d %H:%M:%S.%f')[:-4]
        user.save()
        user_mode.save()
        user_mode.msg_apart_mode = False
        new_neighbor_report(update, context, created_user=user)
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton('Меню',
                                                                   callback_data='_menu')]])
        update.callback_query.message.reply_text(text="Данные сохранены.",
                                                 parse_mode=ParseMode.HTML,
                                                 reply_markup=reply_markup)
        # user_created_report(update, context, created_user=user, text=text)


def save_user_data(update, context):
    """callbackQuery from reject. save user data"""
    log.info(log_msg(update))
    user = chosen_owns(update)
    if not user.updated:
        text = 'В базу ДОБАВЛЕН:\n'
    else:
        text = 'В базе ОБНОВЛЕН:\n'

    if update.callback_query.data == '_apart_reject':
        user_mode = Show.get(user_id=update.effective_user.id)
        user_mode.msg_apart_mode = False
        user.apartment = None
        user_mode.save()
        update.callback_query.message.reply_text(
            text='Квартиру не сохраняем пока что.')

    user.updated = datetime.now().strftime('%y.%m.%d %H:%M:%S.%f')[:-4]
    user.save()

    # TODO: properly do user_created_report
    # user_created_report(update, context, created_user=user, text=text)
    new_neighbor_report(update, context, created_user=user)
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton('Меню',
                                                               callback_data='_menu')]])
    update.callback_query.message.reply_text(text="Данные сохранены.",
                                             parse_mode=ParseMode.HTML,
                                             reply_markup=reply_markup)


def show_house(update, _):
    """callbackQuery handler """
    # TODO: rework that func completely
    log.info(log_msg(update))
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton('Меню',
                                                               callback_data='_menu')]])

    if update.callback_query.data == 'show_this_house':
        # if user want see selected house
        user_query = Show.get(user_id=update.effective_user.id)
    else:
        # if user want see own house and have one
        user_query = chosen_owns(update)
    neighbors = []
    sections = User.select(User.section).where(User.house ==
                                               user_query.house).distinct().order_by(User.section)
    for i in sections:
        neighbors.append('\n' + '📭 <b>Подъезд '.rjust(30, ' ') + str(i.section) + '</b>' + '\n')
        for user in User.select().where(User.house == user_query.house,
                                        User.section == i.section).order_by(User.floor):
            neighbors.append(str(user) + '\n')
    show_list = ('<b>Жители дома №' + str(user_query.house) + '</b>:\n'
                 + '{}' * len(neighbors)).format(*neighbors)

    if len(show_list) < 6200:
        update.message.reply_text(parse_mode=ParseMode.HTML,
                                  text=show_list,
                                  reply_markup=reply_markup)
    else:
        part_1, part_2, part_3 = \
            show_list.partition('📭 <b>Подъезд №4'.rjust(30, ' ') + '</b>' + '\n')
        update.message.reply_text(parse_mode=ParseMode.HTML,
                                  text=part_1[:-2])
        # to do: remove "." from 2nd msg. Without that dot doesn't work
        update.message.reply_text(parse_mode=ParseMode.HTML,
                                  text='.' + part_2 + part_3,
                                  reply_markup=reply_markup)
    update.callback_query.answer()


def show_section(update, _, some_section=False):
    """Here need some documentation"""
    # TODO: rework that func completely
    log.info(log_msg(update))
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton('Меню',
                                                               callback_data='_menu')]])

    if not some_section:
        user_query = chosen_owns(update)
    else:
        user_query = Show.get(user_id=update.effective_user.id)

    query = User.select().where(
        User.house == user_query.house,
        User.section == user_query.section).order_by(User.floor)
    neighbors = [str(user) + '\n' for user in query]

    show_list = (
            '<b>Жители подъезда № ' + str(user_query.section) + ' Дома № ' + str(user_query.house) + '</b>:\n'
            + '{}' * len(neighbors)).format(*neighbors)

    update.message.reply_text(parse_mode=ParseMode.HTML,
                              disable_web_page_preview=True,
                              text=show_list,
                              reply_markup=reply_markup)
    update.callback_query.answer()


def catch_err(update, _, error):
    """handle all telegram errors end send report.
    There is no 'update' so can't logging much info"""
    log.info(f'{error} {type(error)}')
    user_id = update.effective_user.id if update else 'no update'
    try:
        raise error
    except Unauthorized:
        update.message.reply_text(chat_id=ADMIN_ID,
                                  text=f'ERROR:\n {error}\n type {type(error)} id: {user_id}')
    except BadRequest:
        update.message.reply_text(chat_id=ADMIN_ID,
                                  text=f'ERROR:\n {error}\n type {type(error)} id: {user_id}')
    except (TimedOut, NetworkError, TelegramError):
        update.message.reply_text(chat_id=ADMIN_ID,
                                  text=f'ERROR:\n {error}\n type {type(error)} id: {user_id}')


# to do: apply to more then 1 custom filter
@run_async
def del_msg(update, _):
    """message text handler for specific words
    in group chats MessageHandler((Filters.group & block_filter).
    See filters in classes module
    """
    chat_id = update.message.chat_id
    message_id = update.message.message_id
    pattern = block_filter(update.message)
    warn_msg = f'Сообщения, что содержат <code>{pattern}</code> матюк - удаляются автоматически.'

    update.message.reply_text(chat_id=chat_id,
                              message_id=message_id)
    deleted_msg = update.message.reply_text(chat_id=chat_id,
                                            parse_mode=ParseMode.HTML,
                                            text=warn_msg)
    time.sleep(5)
    update.message.reply_text(chat_id=chat_id,
                              message_id=deleted_msg.message_id)
    log.info(log_msg(update) + f' {pattern}')


@run_async
def greeting(update, _):
    """handle new chat members, and sent greeting message.
    Delete after delay. Running async"""
    log.info(log_msg(update))
    new_member_name = update.message.new_chat_members[0].full_name
    text = greeting_msg.format(new_member_name)
    update.message.reply_text(text=text,
                              parse_mode=ParseMode.HTML,
                              disable_web_page_preview=True)


def prepare_data():
    """Create show_list (string) for statistic message,
    and pie_values (list) for chart.
    return from func if no users in db"""
    # TODO: rework prepare data function
    log.info('this func has no update')
    query = User.select()
    query_with = query.where(User.house, User.section)
    query_without = query.where(User.house.is_null() | User.section.is_null())
    houses = query_with.select(User.house).distinct().order_by(User.house)

    # did users indicate their info
    introduced = {'Yes': query_with.count(), 'No': query_without.count()}
    # last 3 joined users
    last_3_users = list(reversed(query_with.order_by(User.id)[-3:]))

    if not last_3_users:
        return

    neighbors = []
    pie_values = []
    bars_values = {}
    for house_ in houses:
        count = query_with.where(User.house == house_.house).count()
        pie_values.append((house_.house, count))
        neighbors.append('\n' + '🏠 <b>Дом '.rjust(30, ' ') + f'{house_.house}</b> <code>({count})</code>\n')
        sections = query_with.select(User.section).where(User.house == house_.house).distinct().order_by(User.section)
        section_dict = {}
        for section_ in sections:
            count = query_with.where(User.house == house_.house, User.section == section_.section).count()
            neighbors.append(f'Подъезд {section_.section} <code>({count})</code>\n')
            section_dict[section_.section] = count
        bars_values[house_.house] = section_dict

    show_list = (f'<b>Всего пользователей: {query.count()}</b>\n'
                 f'<i>Данные указаны {introduced["Yes"]}</i>\n'
                 f'<i>Данные не указаны {introduced["No"]}</i>\n'
                 + '{}' * len(neighbors)).format(*neighbors) + '\n<b>Новые соседи</b>'

    # add to msg last 3 joined users
    for i in range(len(last_3_users)):
        show_list += f'\n{last_3_users[i].joined_str()}'

    return {'show_list': show_list, 'pie_values': pie_values,
            'bars_values': bars_values, 'introduced': introduced}


def statistics(update, _):
    """callbackQuery handler. pattern:^statistics$"""
    log.info(log_msg(update))
    update.callback_query.answer()
    keyboard = [[InlineKeyboardButton('Меню', callback_data='_menu'),
                 InlineKeyboardButton('Графика', callback_data='charts')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    show_list = prepare_data()['show_list']
    update.message.reply_text(parse_mode=ParseMode.HTML,
                              text=show_list,
                              reply_markup=reply_markup)


def make_pie(prepared_data):
    """create pie total by houses"""
    log.info('this func has no update')

    # func for setting values format on pie
    def make_autopct(values):
        def my_autopct(pct):
            total = sum(values)
            val = int(round(pct * total / 100.0))
            return val

        return my_autopct

    # pie by house    
    values = [i[1] for i in prepared_data['pie_values']]
    labels = [f'Буд. {i[0]}' for i in prepared_data['pie_values']]

    fig = plt.figure(figsize=(10, 7))
    mpl.rcParams.update({'font.size': 20})
    plt.pie(values, autopct=make_autopct(values), radius=1.5, pctdistance=0.8,
            shadow=True, labels=labels, labeldistance=1.05)

    img_path = os.path.join('img', 'charts', '1_pie.png')
    fig.savefig(img_path)
    plt.clf()
    plt.close()

    # pie by introduced
    values = list(prepared_data['introduced'].values())
    labels = list(prepared_data['introduced'].keys())

    fig = plt.figure(figsize=None)
    mpl.rcParams.update({'font.size': 16})
    plt.title('Пользователи указали свои данные', pad=15)
    plt.pie(values, autopct=make_autopct(values), radius=1.3, pctdistance=0.8,
            shadow=True, labels=labels, labeldistance=1.05)

    img_path = os.path.join('img', 'charts', '2_pie.png')
    fig.savefig(img_path)
    plt.clf()
    plt.close()


def make_bars(prepared_data):
    """create bars for houses sections count"""
    log.info('this func has no update')
    values_ = prepared_data['bars_values']

    def autolabel(rects, height_factor):
        for i, rect in enumerate(rects):
            height = rect.get_height()
            label = '%d' % int(height)
            ax.text(rect.get_x() + rect.get_width() / 2., height_factor * height,
                    '{}'.format(label),
                    ha='center', va='bottom')

    mpl.rcParams.update({'font.size': 15})

    for house in values_:
        sections = [f'Подъезд {i[-1]}' for i in houses_arr[f'house_{house}']]
        values = [values_[house].get(int(i[-1]), 0) for i in sections]

        plt.bar(sections, values)
        ax = plt.gca()
        ax.set_title(f'Дом {house}')
        autolabel(ax.patches, height_factor=0.85)

        img_path = os.path.join('img', 'charts', f'bar{house}.png')
        plt.savefig(img_path, dpi=200)
        plt.clf()
        plt.close()


@send_typing_action
def charts(update, _):
    """callbackQuery handler. pattern:^charts$. Show chart"""
    log.info(log_msg(update))
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton('Меню', callback_data='_menu')]])

    prepared_data = prepare_data()
    make_pie(prepared_data)
    make_bars(prepared_data)

    charts_dir = os.path.join('img', 'charts')
    charts_list = sorted([f for f in os.listdir(charts_dir) if not f.startswith('.')])
    media = [InputMediaPhoto(open(os.path.join('img', 'charts', i), 'rb')) for i in charts_list]

    update.message.reply_text(media=media)
    update.message.reply_text(parse_mode=ParseMode.HTML,
                              reply_markup=reply_markup,
                              text='Вернуться в меню:')
    update.callback_query.answer()


def notifications_kbd(update, _):
    """callbackQuery handler. pattern:^notifications$. Show notifications keyboard settings"""
    log.info(log_msg(update))
    keyboard = [[InlineKeyboardButton('В моем доме 🏠', callback_data='_notify_house')],
                [InlineKeyboardButton('В моем подъезде 🔢', callback_data='_notify_section')],
                [InlineKeyboardButton('Выключить оповещения 🔕', callback_data='_notify_OFF')],
                [InlineKeyboardButton('Меню', callback_data='_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    user = Show.get(user_id=update.effective_user.id)
    _dict = {None: 'Выключено', '_notify_OFF': 'Выключено',
             '_notify_section': 'В моем подъезде 🔢', '_notify_house': 'В моєм доме 🏠'}
    text = f'Сейчас оповещения установлены в режим\n' \
        f'<b>{_dict[user.notification_mode]}</b>\nПолучать оповещения ' \
           f'когда появится новый сосед:'
    update.message.reply_text(parse_mode=ParseMode.HTML,
                              text=text,
                              reply_markup=reply_markup,
                              message_id=update.effective_message.message_id)
    update.callback_query.answer()


def notifications_save(update, _):
    """callbackQuery handler. pattern: from notifications_kbd func.
    Save notifications settings to db"""
    log.info(log_msg(update))
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton('Меню',
                                                               callback_data='_menu')]])

    user = Show.get(user_id=update.effective_user.id)
    user.notification_mode = update.callback_query.data
    user.save()
    update.message.reply_text(text='Ок! Настройки сохранены',
                              chat_id=update.effective_chat.id,
                              parse_mode=ParseMode.HTML,
                              message_id=update.effective_message.message_id,
                              reply_markup=reply_markup)
    update.callback_query.answer()


def del_command(bot, update):
    """For deleting commands sent in group chat.
    MessageHandler(Filters.command & Filters.group).
    If so - delete message from group chat. """
    command = re.sub(r'@.*', '', update.message.text)
    log.info(log_msg(update) + f' DEL {command}')
    chat_id = update.message.chat_id
    message_id = update.message.message_id
    bot.deleteMessage(chat_id=chat_id, message_id=message_id)
    commands = {'/start': start_command,
                '/help': help_command,
                '/about': about_command}
    try:
        commands[command](bot, update)
    except KeyError:
        # TODO: catch KeyError correctly and pass to logger
        pass


def talkative(update, _):
    """Statistics for messaging in group chat.
    Show top 10 by msgs and by chars"""
    log.info(log_msg(update))
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton('Меню',
                                                               callback_data='_menu')]])

    log_files_list = [f for f in os.listdir('logfiles') if not f.startswith('.')]
    data = {}
    id_pattern = r' ([0-9]{6,10}) '
    pattern = r' ([0-9]{6,10}) name: (.*) usrnm: '

    for log_file in log_files_list:
        with open(os.path.join('logfiles', log_file), mode='r', encoding='utf-8') as file:
            text = file.read()
            match = list(set(re.findall(pattern, text)))
            data = {i[0]: [0, 0, i[1]] for i in match}

    for log_file in log_files_list:
        with open(os.path.join('logfiles', log_file), mode='r', encoding='utf-8') as file:
            for line in file.readlines():
                try:
                    id_ = re.search(id_pattern, line).group().strip()
                    data[id_][0] += len(line.split('msg: ')[1].strip())
                    data[id_][1] += 1
                except (KeyError, AttributeError):
                    pass

    by_chars = sorted(data.items(), key=lambda x: x[1][0], reverse=True)
    by_msgs = sorted(data.items(), key=lambda x: x[1][1], reverse=True)

    template = '<a href="tg://user?id={}">{}</a> {}'

    talkatives_chars = [template.format(user[0], user[1][2], user[1][0]) + '\n' for user in by_chars[:10]]
    talkatives_msgs = [template.format(user[0], user[1][2], user[1][1]) + '\n' for user in by_msgs[:10]]

    show_list = ('<b>Лидеры по количеству знаков</b>\n' + '{}'
                 * len(talkatives_chars)).format(*talkatives_chars) + '\n' + \
                ('<b>Лидеры по количеству сообщений</b>\n' + '{}' * len(talkatives_msgs)).format(
        *talkatives_msgs)

    update.message.reply_text(parse_mode=ParseMode.HTML,
                              disable_web_page_preview=True,
                              text=show_list,
                              reply_markup=reply_markup)


def main():
    updater = Updater(KEY, use_context=True)

    dispatcher = updater.dispatcher
    # group filters
    dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members, greeting))
    dispatcher.add_handler(MessageHandler((Filters.command & Filters.group), del_command))
    dispatcher.add_handler(MessageHandler((Filters.group & block_filter), del_msg))
    dispatcher.add_handler(MessageHandler((Filters.text & Filters.group), group_chat_logging))

    dispatcher.add_handler(CommandHandler("start", start_command))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("about", about_command))

    # TODO: fix problem with custom filters
    # dispatcher.add_handler(MessageHandler(filt_integers, apartment_save))
    # dispatcher.add_handler(MessageHandler(filt_call_err, talkative))
    dispatcher.add_handler(MessageHandler(Filters.text, msg_handler))
    dispatcher.add_handler(CallbackQueryHandler(callback=start_command, pattern='^_menu$'))
    dispatcher.add_handler(CallbackQueryHandler(callback=building, pattern='^building$'))
    dispatcher.add_handler(CallbackQueryHandler(callback=statistics, pattern='^statistics$'))
    dispatcher.add_handler(CallbackQueryHandler(callback=charts, pattern='^charts$'))
    dispatcher.add_handler(CallbackQueryHandler(callback=notifications_kbd,
                                                pattern='^notifications$'))
    dispatcher.add_handler(
        CallbackQueryHandler(callback=notifications_save,
                             pattern='^_notify_section$|^_notify_house$|^_notify_OFF$'))
    dispatcher.add_handler(CallbackQueryHandler(callback=houses_kbd, pattern='^show$'))
    dispatcher.add_handler(CallbackQueryHandler(callback=show_house, pattern='^show_this_house$'))
    dispatcher.add_handler(CallbackQueryHandler(callback=section_kbd, pattern='^p_h'))
    dispatcher.add_handler(CallbackQueryHandler(callback=save_params, pattern='^p_s'))
    dispatcher.add_handler(
        CallbackQueryHandler(callback=check_owns,
                             pattern='^edit$|^house_neighbors$|section_neighbors'))
    dispatcher.add_handler(CallbackQueryHandler(callback=owns_selected, pattern='^set_owns'))
    dispatcher.add_handler(CallbackQueryHandler(callback=set_section_kbd, pattern='^_h'))
    dispatcher.add_handler(
        CallbackQueryHandler(callback=save_user_data,
                             pattern='^_apart_reject$|^_floor_reject$|^_section_reject$'))
    dispatcher.add_handler(CallbackQueryHandler(callback=set_floor_kbd, pattern='^_s'))
    dispatcher.add_handler(CallbackQueryHandler(callback=set_apartment_kbd, pattern='^_f'))

    # dispatcher.add_error_handler(catch_err)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
