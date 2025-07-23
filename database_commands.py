import psycopg2
from psycopg2 import sql
import configparser

class Password:
    """
    Класс для скрытия пароля
    """
    config = configparser.ConfigParser()
    config.read('settings.ini')
    password = config['Passwords']['password']


class DataBase:
    """
    Класс, инкапсулирующий в себя все функции, связанные с манипуляциями с базой данных
    """

    def __init__(self):
        self.conn = psycopg2.connect(database='eng_cards_db', user = 'postgres',password=Password.password)
        self.cur = self.conn.cursor()

    def check_user(self, user_id):
        """
        Функция для проверки наличия данных о пользователе в БД
        """
        self.user_id = user_id
        user1 = 'user_' + str(self.user_id)
        with self.conn:
            self.cur.execute("""SELECT FROM users WHERE name = %s;""", (user1,))
            self.conn.commit()
            return bool(self.cur.fetchall())

    def add_user(self, user_id):
        """
        Функция для добавления данных о пользователе в БД
        """
        self.user_id = user_id
        user1 = 'user_' + str(self.user_id)
        if  not DataBase.check_user(self, self.user_id):
            with self.conn:
                self.cur.execute("""INSERT INTO users (name) VALUES (%s);""", (user1,))
                self.conn.commit()
        else:
            return 'Пользователь уже занесён в базу данных'

    def create_user_table(self, user_id):
        """
        Функция для создания отельной таблицы для каждого пользователя
        """
        self.user_id = user_id
        user1 = 'user_' + str(self.user_id)
        if DataBase.check_user(self, self.user_id):
            with self.conn:
                self.cur.execute(sql.SQL("""CREATE TABLE IF NOT EXISTS {table} as 
                                           (SELECT eng, ru FROM zero);""").format(table=sql.Identifier(user1)))
                try:
                    self.cur.execute(sql.SQL("""ALTER TABLE {table}
                                    ADD COLUMN id SERIAL PRIMARY KEY,
                                    ADD CONSTRAINT eng_only CHECK(eng ~*'[a-z]+'),
                                    ADD CONSTRAINT {en_constraint} UNIQUE (eng),
                                    ALTER COLUMN eng SET NOT NULL,
                                    ADD CONSTRAINT ru_only CHECK(ru ~*'[а-яё]+'),
                                    ALTER COLUMN ru SET NOT NULL;""").format(table=sql.Identifier(user1),
                                                                             en_constraint=sql.Identifier(user1+'en')))
                except:
                    return 'Таблица уже существует'
                self.conn.commit()

        else:
            return 'Что-то пошло не так'

    def check_word(self, new_word, user_id):
        """
        Функция, проверяющая вхождение слова в таблицу пользователя
        """
        self.new_word = new_word
        self.user_id =  user_id
        user1 = 'user_' + str(self.user_id)
        with self.conn:
            self.cur.execute(sql.SQL("""SELECT FROM {table} WHERE eng = %s;""").format(table=sql.Identifier(user1),
                                                                                      ),(new_word,))
            self.conn.commit()
            return bool(self.cur.fetchall())

    def add_word(self, new_word, translate, user_id):
        """
        Фунцкия, добавляющая слово в таблицу пользователя в БД
        """
        self.new_word = new_word
        self.user_id = user_id
        user1 = 'user_' + str(self.user_id)
        self.translate = translate
        if not DataBase.check_word(self, self.new_word, self.user_id):
            with self.conn:
                self.cur.execute(sql.SQL("""INSERT INTO {table} (eng, ru)
                                            VALUES (%s,%s)""").format(table=sql.Identifier(user1)),
                                                         (self.new_word, self.translate))
                self.conn.commit()
                return 'Слово успешно добавлено!'
        else:
            return ('Слово уже есть в списке')

    def delete_word(self, del_word, user_id):
        """
        Функция, удаляющая слово из таблицы пользователя в БД
        """
        self.del_word = del_word
        self.user_id =  user_id
        user1 = 'user_' + str(self.user_id)
        if DataBase.check_word(self, self.del_word, self.user_id):
            with self.conn:
                self.cur.execute(sql.SQL("""DELETE FROM {table} 
                                            WHERE eng = %s""").format(table=sql.Identifier(user1)),
                                                         (self.del_word,))
                self.conn.commit()
                return 'Слово было удалено'
        else:
            return 'Слова нет в списке'

    def get_eng_words(self, user_id):
        """
        Функция для получения списка доступных слов, используется вспомогательно для преобразования в список данных
        из БД
        """
        self.user_id = user_id
        user1 = 'user_' + str(self.user_id)
        if DataBase.check_user(self, self.user_id):
            with self.conn:
                self.cur.execute(sql.SQL("""SELECT eng FROM {table} """).format(table=sql.Identifier(user1)))
                eng_list = []
                for pair in self.cur.fetchall():
                    eng_list.append(pair[0])
                return eng_list
        else:
            return 'Пользователь потерян и не найден'

    def get_translate(self, user_id, target_word):
        """
        Функция для получения перевода слова из БД
        """
        self.user_id = user_id
        self.target_word = target_word
        user1 = 'user_' + str(self.user_id)
        if DataBase.check_user(self, self.user_id):
            with self.conn:
                self.cur.execute(sql.SQL("""SELECT ru FROM {table} 
                 WHERE eng = %s""").format(table=sql.Identifier(user1)), (self.target_word,))
                result = self.cur.fetchone()[0]
                return result





