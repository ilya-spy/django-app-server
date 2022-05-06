
import logging
import sqlite3
import os

from collections import defaultdict
from contextlib import contextmanager
from dataclasses import astuple, fields
from itertools import chain, islice

import psycopg2
from psycopg2.extras import DictCursor

from dotenv import load_dotenv
load_dotenv()
logger = logging.getLogger(__name__)


@contextmanager
def sqlite_manager(dbfile):
    try:
        open(dbfile, 'r')
    except FileNotFoundError:
        logger.error('Can not find sqlite data base file')
        return
    conn = sqlite3.connect(dbfile)
    conn.row_factory = sqlite3.Row
    yield conn

    conn.close()


@contextmanager
def postgres_manager():
    dsl = {
        'dbname':   os.environ.get('POSTGRES_DB'),
        'user':     os.environ.get('POSTGRES_USER'),
        'password': os.environ.get('POSTGRES_PASSWORD'),
        'host':     os.environ.get('POSTGRES_HOST', '127.0.0.1'),
        'port':     os.environ.get('POSTGRES_PORT', 5432),
    }
    conn = psycopg2.connect(**dsl, cursor_factory=DictCursor)
    yield conn

    conn.close()


class SQLiteLoader:
    def __init__(self, sqlite_conn, chunk_size=1000):
        self.__cursor = sqlite_conn.cursor()
        self.__chunk_size = chunk_size
        self.__num_fetched = defaultdict(lambda: 0)

    def fetch_table(self, table: str, target: object):
        # Fetch and save entire table specified
        logger.info(f'Fetching: SELECT * FROM {table};')
        try:
            self.__cursor.execute(f'SELECT * FROM {table};')
        except sqlite3.Error as e:
            logger.error(e)
            return
        while True:
            rows = self.__cursor.fetchmany(size=self.__chunk_size)
            if not rows:
                break
            self.__num_fetched[table] += len(rows)
            logger.info(f'### SQLite read: {len(rows)} rows')

            # Yield data as a target dataclass instance
            yield from [target(**row) for row in rows]

    def len_table(self, table):
        return self.__num_fetched[table]


class PostgresSaver:
    def __init__(self, postgres_conn, chunk_size=1000):
        # Disable autocommit and manual control for speed-up
        self.__connection = postgres_conn
        self.__connection.autocommit = False

        self.__cursor = postgres_conn.cursor()
        self.__chunk_size = chunk_size

    def chunks(self, iterable):
        iterator = iter(iterable)
        for first in iterator:
            yield chain(
                [first],
                islice(iterator, self.__chunk_size - 1)
            )

    def insert_table(self, table: str, values: iter, target: object):
        logger.info(f'### Postgres insert: {table}')

        # Insert all values sliced in chunks
        for chunk in self.chunks(values):
            rows_data = [astuple(i) for i in chunk]
            # check generator is not depleted
            if not rows_data:
                break

            rows_fmt = ','.join(['%s'] * len(rows_data))
            col_names = ','.join(field.name for field in fields(target))
            logger.info(f'### Postgres write: {len(rows_data)} rows')

            src = f'''INSERT INTO content.{table} ({col_names})
                        VALUES {rows_fmt}
                        ON CONFLICT (id) DO NOTHING;
                    '''
            # cursor.mogrify() to produce raw SQL for inserting multiple values
            sql = self.__cursor.mogrify(src, rows_data).decode('utf8')
            logger.debug(f'### Running SQL:\n{sql}')
            self.__cursor.execute(sql)
            # committing changes
            self.__connection.commit()
