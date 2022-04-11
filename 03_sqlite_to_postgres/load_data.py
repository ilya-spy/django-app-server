
from msilib.schema import tables
import sqlite3
import uuid, os
from tkinter.messagebox import NO

from pprint import pprint
from datetime import datetime

from contextlib import contextmanager
from dataclasses import dataclass, field
from dotenv import load_dotenv

import psycopg2
from psycopg2.extensions import connection as _connection
from psycopg2.extras import DictCursor


load_dotenv()

@contextmanager
def sqlite_manager():
    conn = sqlite3.connect(os.environ.get('SQLITE_DB_NAME'))
    conn.row_factory = sqlite3.Row

    yield conn # С конструкцией yield вы познакомитесь в следующем модуле 
    # Пока воспринимайте её как return, после которого код может продолжить выполняться дальше
    conn.close()

@contextmanager
def postgres_manager():
    dsl = {
        'dbname':   os.environ.get('DB_NAME'),
        'user':     os.environ.get('DB_USER'),
        'password': os.environ.get('DB_PASSWORD'),
        'host':     os.environ.get('DB_HOST', '127.0.0.1'),
        'port':     os.environ.get('DB_PORT', 5432),
    }
    conn = psycopg2.connect(**dsl, cursor_factory=DictCursor)
    yield conn
    # Пока воспринимайте её как return, после которого код может продолжить выполняться дальше
    conn.close()


@dataclass
class FilmWork:
    #movie = FilmWork(title='movie', description='new movie', rating=0.0)
    # Обратите внимание: для каждого поля указан тип
    type: str
    title: str
    description: str
    creation_date: datetime
    created_at: datetime
    updated_at: datetime
    # Ещё один бонус: в dataclass вы можете определить значение по умолчанию
    rating: float = field(default=0.0)
    file_path: str = field(default='./')
    id: uuid.UUID = field(default_factory=uuid.uuid4)

@dataclass
class Genre:
    name: str
    description: str
    created_at: datetime
    updated_at: datetime
    id: uuid.UUID = field(default_factory=uuid.uuid4)

@dataclass
class Person:
    full_name: str
    created_at: datetime
    updated_at: datetime
    id: uuid.UUID = field(default_factory=uuid.uuid4)

@dataclass
class GenreFilmWork:
    film_work_id: uuid.UUID
    genre_id: uuid.UUID
    id: uuid.UUID
    created_at: datetime


@dataclass
class PersonFilmWork:
    film_work_id: uuid.UUID
    person_id: uuid.UUID
    role: str
    id: uuid.UUID
    created_at: datetime


class SQLiteLoader:
    def __init__(self, sqlite_conn):
        self.__cursor = sqlite_conn.cursor()
        self.__data = {}

    def fetch_table(self, table: str, Target: object):
        self.__data[table] = []
        # Fetch and save entire table specified
        self.__cursor.execute("SELECT * FROM {tname};".format(tname=table))
        self.__data[table] = self.__cursor.fetchall()
        self.__data[table] =  list(map(lambda fw:
            Target(
                **dict(zip(fw.keys(), tuple(fw)))
            ),
            self.__data[table]))

    def get_table(self, table):
        return self.data[table]

    def len_table(self, table):
        return len(self.__data[table])

    def row_table(self, table, idx):
        if idx < self.len_table(table):
            return self.__data[table][idx]


class PostgresSaver:
    def __init__(self, postgres_conn):
        self.connection = postgres_conn

    def insert_chunk(self, table, data, Target, size=50):
        sql = '''
            INSERT INTO content.{tname} (id, name) 
            VALUES 
                ('b8531efb-c49d-4111-803f-725c3abc0f5e', 'Василий Васильевич'),
                ('2d5c50d0-0bb4-480c-beab-ded6d0760269', 'Пётр Петрович'),
                ON CONFLICT (id) DO NOTHING;
            '''.format(tname=table)



if __name__ == '__main__':
    with sqlite_manager() as sqlt_conn, postgres_manager() as psg_conn:
        loader = SQLiteLoader(sqlt_conn)

        loader.fetch_table('film_work', FilmWork)
        print('\n### film_work: ', loader.len_table('film_work'))
        print('\n', loader.row_table('film_work', 8))
        print('\n', loader.row_table('film_work', 98))
        print('\n', loader.row_table('film_work', 998))

        loader.fetch_table('person', Person)
        print('\n### person: ', loader.len_table('person'))
        print('\n', loader.row_table('person', 8))
        print('\n', loader.row_table('person', 98))
        print('\n', loader.row_table('person', 998))

        loader.fetch_table('genre', Genre)
        print('\n### genre: ', loader.len_table('genre'))
        print('\n', loader.row_table('genre', 8))
        print('\n', loader.row_table('genre', 19))
        print('\n', loader.row_table('genre', 25))

        loader.fetch_table('genre_film_work', GenreFilmWork)
        print('\n### genre_film_work: ', loader.len_table('genre_film_work'))
        print('\n', loader.row_table('genre_film_work', 8))
        print('\n', loader.row_table('genre_film_work', 19))
        print('\n', loader.row_table('genre_film_work', 25))

        loader.fetch_table('person_film_work', PersonFilmWork)
        print('\n### person_film_work: ', loader.len_table('person_film_work'))
        print('\n', loader.row_table('person_film_work', 8))
        print('\n', loader.row_table('person_film_work', 98))
        print('\n', loader.row_table('person_film_work', 998))
