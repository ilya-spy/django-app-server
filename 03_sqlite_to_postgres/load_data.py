
import sqlite3
import uuid
import os

from datetime import datetime

from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass, field, astuple, fields
from dotenv import load_dotenv

import psycopg2
from psycopg2.extras import DictCursor


load_dotenv()


@contextmanager
def sqlite_manager():
    conn = sqlite3.connect(os.environ.get('SQLITE_DB_NAME'))
    conn.row_factory = sqlite3.Row
    yield conn

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

    conn.close()


@dataclass
class FilmWork:
    # movie = FilmWork(title='movie', description='new movie', rating=0.0)
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

    # Fixes for schema inconsistencies when importing
    def __post_init__(self):
        # Replace, if NULL provided from source
        self.creation_date = self.creation_date or \
            datetime.fromisoformat('2001-01-01')
        self.file_path = self.file_path or './' + \
            self.title.replace(' ', '')
        # Replace description, if NULL provided from source
        self.description = self.description or 'Yet another filmwork...'
        # Replace description, if NULL provided from source
        self.rating = self.rating or 5.0


@dataclass
class Genre:
    name: str
    description: str
    created_at: datetime
    updated_at: datetime
    id: uuid.UUID = field(default_factory=uuid.uuid4)

    # Fixes for schema inconsistencies when importing
    def __post_init__(self):
        # Replace description, if NULL provided from source
        self.description = self.description or 'Yet another genre...'


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
        self.__data = defaultdict(lambda: [])

    def fetch_table(self, table: str, Target: object):
        # Fetch and save entire table specified
        self.__cursor.execute("SELECT * FROM {tname};".format(tname=table))
        self.__data[table] = self.__cursor.fetchall()
        if not len(self.__data[table]):
            return
        # Save data into Target dataclass
        self.__data[table] = list(map(lambda fw:
                                      Target(
                                          **dict(zip(fw.keys(), tuple(fw)))
                                      ),
                                      self.__data[table]))

    def get_table(self, table):
        return self.__data[table]

    def len_table(self, table):
        return len(self.__data[table])

    def row_table(self, table, idx):
        if idx < self.len_table(table):
            return self.__data[table][idx]


class PostgresSaver:
    def __init__(self, postgres_conn, chunk_size=50, verbose=False):
        # Disable autocommit and manual control for speed-up
        self.__connection = postgres_conn
        self.__connection.autocommit = False

        self.__cursor = postgres_conn.cursor()
        self.__chunk_size = chunk_size
        self.__verbose = verbose

    def chunks(self, lst):
        """Yield successive n-sized chunks from lst."""
        for i in range(0, len(lst), self.__chunk_size):
            yield lst[i:i + self.__chunk_size]

    def insert_table(self, table, values, Target):
        print('### Processing insert: {}'.format(table))
        # Insert all values sliced in chunks
        for chunk in self.chunks(values):
            rows_data = [astuple(i) for i in chunk]
            rows_fmt = ','.join(['%s'] * len(chunk))
            col_names = ','.join(field.name for field in fields(Target))

            src = '''INSERT INTO content.{tname} ({columns})
                        VALUES {rows}
                        ON CONFLICT (id) DO NOTHING;
                    '''.format(tname=table, columns=col_names, rows=rows_fmt)
            # cursor.mogrify() to produce raw SQL for inserting multiple values
            sql = self.__cursor.mogrify(src, rows_data).decode('utf8')
            if self.__verbose:
                print('### Running SQL:\n', sql)
            self.__cursor.execute(sql)
            # committing changes
            self.__connection.commit()


if __name__ == '__main__':
    with sqlite_manager() as sqlt_conn, postgres_manager() as psg_conn:
        loader = SQLiteLoader(sqlt_conn)

        loader.fetch_table('film_work', FilmWork)
        print('### film_work: ', loader.len_table('film_work'))
        loader.fetch_table('person', Person)
        print('### person: ', loader.len_table('person'))
        loader.fetch_table('genre', Genre)
        print('### genre: ', loader.len_table('genre'))
        loader.fetch_table('genre_film_work', GenreFilmWork)
        print('### genre_film_work: ', loader.len_table('genre_film_work'))
        loader.fetch_table('person_film_work', PersonFilmWork)
        print('### person_film_work: ', loader.len_table('person_film_work'))

        print('\n### Starting Postgres import...\n')
        saver = PostgresSaver(psg_conn)
        saver.insert_table('genre', loader.get_table('genre'), Genre)
        saver.insert_table('person', loader.get_table('person'), Person)
        saver.insert_table('film_work',
                           loader.get_table('film_work'), FilmWork)
        saver.insert_table('genre_film_work',
                           loader.get_table('genre_film_work'), GenreFilmWork)
        saver.insert_table('person_film_work', loader.
                           get_table('person_film_work'), PersonFilmWork)
        print('\n### DONE Postgres import...\n')
