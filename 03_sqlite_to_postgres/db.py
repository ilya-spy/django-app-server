
import logging
import sqlite3
import os

from collections import defaultdict
from contextlib import contextmanager
from dataclasses import astuple, fields
from dotenv import load_dotenv

import psycopg2
from psycopg2.extras import DictCursor


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
        'dbname':   os.environ.get('DB_NAME'),
        'user':     os.environ.get('DB_USER'),
        'password': os.environ.get('DB_PASSWORD'),
        'host':     os.environ.get('DB_HOST', '127.0.0.1'),
        'port':     os.environ.get('DB_PORT', 5432),
    }
    conn = psycopg2.connect(**dsl, cursor_factory=DictCursor)
    yield conn

    conn.close()


class SQLiteLoader:
    def __init__(self, sqlite_conn):
        self.__cursor = sqlite_conn.cursor()
        self.__data = defaultdict(lambda: [])

    def fetch_table(self, table: str, target: object):
        # Fetch and save entire table specified
        logger.info(f'Fetching: SELECT * FROM {table};')
        self.__cursor.execute(f'SELECT * FROM {table};')

        self.__data[table] = self.__cursor.fetchall()
        if not len(self.__data[table]):
            return

        # Save data into target dataclass
        self.__data[table] = list(map(lambda fw:
                                      target(
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
    def __init__(self, postgres_conn, chunk_size=50):
        # Disable autocommit and manual control for speed-up
        self.__connection = postgres_conn
        self.__connection.autocommit = False

        self.__cursor = postgres_conn.cursor()
        self.__chunk_size = chunk_size

    def chunks(self, lst):
        """Yield successive n-sized chunks from lst."""
        for i in range(0, len(lst), self.__chunk_size):
            yield lst[i:i + self.__chunk_size]

    def insert_table(self, table: str, values: list, target: object):
        logger.info(f'### Postgres insert: {table}')

        # Insert all values sliced in chunks
        for chunk in self.chunks(values):
            rows_data = [astuple(i) for i in chunk]
            rows_fmt = ','.join(['%s'] * len(chunk))
            col_names = ','.join(field.name for field in fields(target))

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
