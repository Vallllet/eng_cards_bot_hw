import random
import re

from telebot import types, TeleBot, custom_filters
from telebot.storage import StateMemoryStorage
from telebot.handler_backends import State, StatesGroup
from database_commands import DataBase
import configparser


class Tokens:
    """
    Класс Token для того, чтобы скрыть токен от Github'a
    """
    config = configparser.ConfigParser()
    config.read('settings.ini')
    token = config['Tokens']['bot_token']


state_storage = StateMemoryStorage()
token_bot = Tokens.token
bot = TeleBot(token_bot, state_storage=state_storage)
DB = DataBase()

known_users = {}


class UserInfo:
    """
    Класс для хранения информации о пользователе в момент текущей сессии
    """
    def __init__(self, user_id):
        self.user_id = user_id
        self.buttons = []
        self.random_control = []
        self.eng_word = ''
        if self.user_id not in known_users:
            known_users[self.user_id] = self


print('Start telegram bot...')


def show_hint(*lines):
    """
    Вспомогательная функция для вывода информации.
    Принимает строки lines, выводит их с переносом строки.
    """
    return '\n'.join(lines)


def show_target(data):
    """
    Ещё одна вспомогательная функция для отображения данных,
    выводит отображение слово > перевод.
    """
    return f"{data['target_word']} -> {data['translate_word']}"


class Command:
    """
    Класс с командами (хранит названия кнопок)
    """
    ADD_WORD = 'Добавить слово ➕'
    DELETE_WORD = 'Удалить слово🔙'
    NEXT = 'Дальше ⏭'
    HELP = '/help'
    CARDS = '/cards'


class MyStates(StatesGroup):
    """
    Класс с состояниями
    """
    target_word = State()
    translate_word = State()
    another_words = State()


@bot.message_handler(commands=['start'])
def greetings(message):
    """
    Команда приветствия, учитывает, новый пользователь
    или старый решил снова написать /start
    Приветствует пользователя и предлагает 2 кнопки на выбор
    Справка предлагается по команде /help
    """
    cid = message.chat.id
    uid = message.from_user.id
    help_button = types.KeyboardButton(Command.HELP)
    cards_button = types.KeyboardButton(Command.CARDS)
    button_list = [help_button, cards_button]
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add(*button_list)
    UserInfo(uid)
    if DB.check_user(uid) is False:
        DB.add_user(uid)
        DB.create_user_table(uid)
        bot.send_message(cid, f"Здравствуй, user_{uid}, "
                              f"давай изучать английский...\n"
                              "Введи /help для справки!", reply_markup=markup)
    else:
        bot.send_message(cid, f"Снова здравствуй, user_{uid}, "
                              f"давай изучать английский...\n"
                              "Введи /cards для продолжения!",
                         reply_markup=markup)


@bot.message_handler(commands=['help'])
def help_command(message):
    """
    Справка
    """
    uid = message.from_user.id
    UserInfo(uid)
    hello = ('Я могу помочь тебе с изучением английского!\n'
             'Команда /cards — для начала изучения, '
             'список слов у тебя свой!\n'
             'После этой команды Я буду предлагать тебе слова,'
             ' а тебе нужно выбрать правильное!\n'
             'Есть команды "Добавить слово" и "Удалить слово"'
             ' для редактирования списка слов.\n'
             'Есть команда "Дальше", она позволяет пропустить '
             'текущее слово и перейти к следующему.\n'
             'Обязательно выполняйте инструкции полностью! '
             'Особенно по написанию слов.\n'
             'Удачного изучения!')
    bot.send_message(message.chat.id, hello)


@bot.message_handler(commands=['cards'])
def create_cards(message):
    """
    Создаёт карты с английскими словами, опираясь на базу данных
    Создаёт кнопки
    Учитывает прогресс в сессии и не позволяет
    существовать большому количеству повторов
    """
    uid = message.from_user.id
    UserInfo(uid)
    markup = types.ReplyKeyboardMarkup(row_width=2)
    known_users[uid].buttons = []
    all_words = random.sample(DB.get_eng_words(uid), 4)
    target_word = all_words[0]
    translate = DB.get_translate(uid, target_word)
    while target_word in known_users[uid].random_control:
        all_words = random.sample(DB.get_eng_words(uid), 4)
        target_word = all_words[0]
        translate = DB.get_translate(uid, target_word)
    if target_word not in known_users[uid].random_control:
        known_users[uid].random_control.append(target_word)
    if len(known_users[uid].random_control) == len(DB.get_eng_words(uid)) - 1:
        known_users[uid].random_control = []
    target_word_btn = types.KeyboardButton(target_word)
    known_users[uid].buttons.append(target_word_btn)
    others = all_words[1:4]
    other_words_btns = [types.KeyboardButton(word) for word in others]
    known_users[uid].buttons.extend(other_words_btns)
    random.shuffle(known_users[uid].buttons)
    next_btn = types.KeyboardButton(Command.NEXT)
    add_word_btn = types.KeyboardButton(Command.ADD_WORD)
    delete_word_btn = types.KeyboardButton(Command.DELETE_WORD)
    known_users[uid].buttons.extend([next_btn, add_word_btn, delete_word_btn])
    markup.add(*known_users[uid].buttons)
    greeting = f"Выбери перевод слова:\n🇷🇺 {translate}"
    bot.send_message(message.chat.id, greeting, reply_markup=markup)
    bot.set_state(message.from_user.id, MyStates.target_word, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['target_word'] = target_word
        data['translate_word'] = translate
        data['other_words'] = others


@bot.message_handler(func=lambda message: message.text == Command.NEXT)
def next_cards(message):
    """
    Перезапускает функцию создания карт, пропуская слово
    """
    uid = message.from_user.id
    UserInfo(uid)
    create_cards(message)


@bot.message_handler(func=lambda message: message.text == Command.DELETE_WORD)
def delete_initiation(message):
    """
    Функция для удаления слова из базы данных
    Принимает сообщение со словом от пользователя,
    обрабатывает его в случае, если слово было в списке.
    """
    uid = message.from_user.id
    UserInfo(uid)
    msg = bot.reply_to(message, text='Введите слово, '
                                     'которое хотите удалить '
                                     '(ввести нужно слово '
                                     'на английском языке)')
    bot.register_next_step_handler(msg, delete_word)


def delete_word(message):
    """
    Вспомогательная функция для первой
    """
    uid = message.from_user.id
    word = message.text.lower()
    if DB.get_words_count(uid) == 4:
        bot.reply_to(message, 'Слов осталось слишком мало...')
        return next_cards(message)
    if DB.delete_word(word, uid) == 'Слова нет в списке':
        bot.reply_to(message, 'Не получилось... Вы уверены, '
                              'что корректно ввели слово?')
        create_cards(message)
    else:
        bot.reply_to(message, 'Слово успешно удалено')
        create_cards(message)


@bot.message_handler(func=lambda message: message.text == Command.ADD_WORD)
def add_word_initiate(message):
    """
    Функции для добавления слова
    Учитывают, что слово должно быть написано на верном языке
    Обрабатываются 2-мя сообщениями после старта команды
    """
    uid = message.from_user.id
    UserInfo(uid)
    msg = bot.reply_to(message, text='Введите слово, '
                                     'которое хотите добавить '
                                     '(ввести нужно слово '
                                     'на английском языке)')
    bot.register_next_step_handler(msg, add_eng_word)


def add_eng_word(message):
    """
    Вспомогательная функция(проверка и принятие английского слова)
    """
    uid = message.from_user.id
    known_users[uid].eng_word = message.text.lower()
    pattern = r"[a-zA-Z]+"
    if re.fullmatch(pattern, known_users[uid].eng_word):
        if DB.check_word(known_users[uid].eng_word, uid) is True:
            bot.reply_to(message, text='Слово уже изучается!')
            create_cards(message)
        else:
            msg = bot.reply_to(message, text='Отлично! '
                                             'Теперь нужно ввести перевод!')
            bot.register_next_step_handler(msg, add_ru_word)
    else:
        bot.reply_to(message, text='Слово должно быть на английском языке!')


def add_ru_word(message):
    """
    Вспомогательная функция
    (проверка и принятие русского слова)
    """
    uid = message.from_user.id
    pattern = r"[а-яёА-ЯЁ]+"
    ru_word = message.text.lower()
    if re.fullmatch(pattern, ru_word):
        if (DB.add_word(known_users[uid].eng_word, ru_word, uid)
                == 'Слово успешно добавлено!'):
            bot.reply_to(message, text='Слово успешно добавлено!'
                                       f'Количество изучаемых слов: '
                                       f'{DB.get_words_count(uid)}')
            next_cards(message)
        else:
            bot.reply_to(message, text='Это слово уже используется '
                                       'в качестве перевода!\n'
                                       '(простите, мы ограничены '
                                       'технической базой '
                                       'для того, чтобы у одного слова '
                                       'был множественный перевод)')

            next_cards(message)
    else:
        bot.reply_to(message, text='Слово должно быть на русском языке!')


@bot.message_handler(func=lambda message: True, content_types=['text'])
def message_reply(message):
    """
    Функция для восприятия ботом текста
    Учитывает угадывание слов из команды create_cards
    """
    uid = message.from_user.id
    UserInfo(uid)
    text = message.text
    markup = types.ReplyKeyboardMarkup(row_width=2)
    try:
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            target_word = data['target_word']
            if text == target_word:
                hint = show_target(data)
                hint_text = ["Отлично!❤", hint]
                hint = show_hint(*hint_text)
            else:
                for btn in UserInfo(uid).buttons:
                    if btn.text == text:
                        btn.text = text + '❌'
                        break
                hint = show_hint("Допущена ошибка!",
                                 f"Попробуй ещё раз вспомнить "
                                 f"слово 🇷🇺{data['translate_word']}")
    except KeyError:
        hint = "Мы ещё не начали работу! Введи команду /cards!"
    markup.add(*known_users[uid].buttons)
    bot.send_message(message.chat.id, hint, reply_markup=markup)
    try:
        if text == target_word:
            create_cards(message)
    except UnboundLocalError:
        pass


bot.add_custom_filter(custom_filters.StateFilter(bot))

bot.infinity_polling(skip_pending=True)
