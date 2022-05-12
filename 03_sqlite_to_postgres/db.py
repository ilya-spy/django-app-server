
import logging
import sqlite3
import os

from collections import defaultdict
from contextlib import contextmanager
from dataclasses import astuple, fields
from itertools import chain, islice
from datetime import datetime

import psycopg2
from psycopg2.extras import DictCursor

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel('INFO')


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

def chunks(iterable, chunk_size):
    iterator = iter(iterable)
    for first in iterator:
        yield chain(
            [first],
            islice(iterator, chunk_size - 1)
        )

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

    def insert_table(self, table: str, values: iter, target: object):
        logger.info(f'### Postgres insert: {table}')

        # Insert all values sliced in chunks
        for chunk in chunks(values, self.__chunk_size):
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


class PostgresETL:
    def __init__(self, model, postgres_conn, chunk_size=1000):
        self.connection = postgres_conn
        self.cursor = postgres_conn.cursor()
        self.chunk_size = chunk_size
        self.num_fetched = 0

        self.model = model
        self.keystore = os.environ.get('DJANGO_DATA_DIR')
    
    def extract(self, query):
        # exceptions should be handled on app level
        logger.debug(f'### Extractor: Running SQL query:\n{query}')
        self.cursor.execute(query)
        while True:
            rows = self.cursor.fetchmany(self.chunk_size)
            if not rows:
                break
            logger.info(f'### Postgres produced: {len(rows)} rows')
            self.num_fetched += len(rows)
            yield from rows
    
    def num_extracted(self):
        return self.num_fetched

class PostgresProducer(PostgresETL):
    def __init__(self, model, postgres_conn, startdate=None, chunk_size=1000):
        super().__init__(model, postgres_conn, chunk_size)

        if type(startdate) == datetime:
            self.startdate = startdate
            return

        self.last_sync = os.path.join(self.keystore, self.model + '.sync')
        if not os.path.exists(self.last_sync): 
            logger.info(
                f'### Extractor: created sync file for {self.model}')
            with open(self.last_sync, 'w') as fp:
                fp.write(datetime.min.strftime("%Y-%m-%d %H:%M:%S"))

        # load latest sync date
        with open(self.last_sync) as f:
            try:
                stamp = f.read()
                logger.info(
                    f'### Extractor: last sync for {self.model}: {stamp}')
                self.startdate = \
                    datetime.strptime(stamp, "%Y-%m-%d %H:%M:%S")

            except:
                self.startdate = datetime.min

    def get_startdate(self):
        'get computed export starting date for the model'
        return self.startdate
    
    def set_startdate(self):
        'set updated sync pointer to mark previous changes done'
        with open(self.last_sync, 'w') as fp:
            self.startdate = datetime.utcnow()
            fp.write(self.startdate.strftime("%Y-%m-%d %H:%M:%S"))

    def produce(self):
        'get records, updated after computed starting date'

        sql = f"SELECT id FROM content.{self.model} \
            WHERE updated_at > '{self.startdate.strftime('%Y-%m-%d %H:%M:%S')}' \
            ORDER BY updated_at;"
        yield from self.extract(sql)


class PostgresEnricher(PostgresETL):
    def __init__(self, model, postgres_conn, chunk_size=1000):
        super().__init__(model, postgres_conn, chunk_size)
        self.target = {}
        self.total_uids = 0

    def find_target(self, updated):
        'find fw records, affected by produced updates to db'

        for chunk in chunks(updated, self.chunk_size):
            ids = list(map(lambda r: r['id'], chunk))
            if not len(ids):
                return
            logger.info(f'### Enricher: new chunk of {len(ids)}, cascading...')

            src = f'SELECT fw.id \
                FROM content.film_work fw \
                LEFT JOIN content.{self.model}_film_work relfw \
                ON relfw.film_work_id = fw.id \
                WHERE relfw.{self.model}_id \
                IN ({",".join(["%s"] * len(ids))}) \
                ORDER BY fw.updated_at'
            sql = self.cursor.mogrify(src, ids).decode('utf8')
            yield from self.extract(sql)
            logger.info(f'### Enricher: find chunk done\n')

    def init_target(self, cascaded):
        # init the elastic dict with unique uid records
        for chunk in chunks(cascaded, chunk_size=500):
            for uid in list(map(lambda r: str(r['id']), chunk)):
                self.total_uids += 1
                self.target[uid] = { 
                    'id': uid, 
                    'actors_names': '',
                    'writers_names': '',
                    'director': '',
                    'actors': [],
                    'writers': [],
                    'genre': [],
                }

    def enrich_target(self):
        # enrich target table, based on proxy relation discovery results
        for chunk in chunks(self.target, self.chunk_size):
            ids = list(chunk)
            if not len(ids):
                return
            logger.info(
                f'### Enricher: new target chunk of {len(ids)},enriching...')

            src = f'SELECT \
                fw.id as fw_id, \
                fw.title, \
                fw.description, \
                fw.rating, \
                pfw.role, \
                p.id as pid, \
                p.full_name, \
                g.name as gname\
                FROM content.film_work fw \
                LEFT JOIN content.person_film_work pfw ON pfw.film_work_id = fw.id \
                LEFT JOIN content.person p ON p.id = pfw.person_id \
                LEFT JOIN content.genre_film_work gfw ON gfw.film_work_id = fw.id \
                LEFT JOIN content.genre g ON g.id = gfw.genre_id \
                WHERE fw.id IN ({",".join(["%s"] * len(ids))});'
            sql = self.cursor.mogrify(src, ids).decode('utf8')
            yield from self.extract(sql)
            logger.info(f'### Enricher: enrich chunk done\n')

    def merge_target(self, enriched):
        # merge joined enriched rows to build unique dicts for elastic
        for chunk in chunks(enriched, chunk_size=500):
            for row in list(chunk):
                id = str(row['fw_id'])
                self.target[id]['description'] = row['description']
                self.target[id]['title'] = row['title']
                self.target[id]['imdb_rating'] = row['rating']

                if row['role'] == 'director':
                    self.target[id]['director'] = row['full_name']

                if row['role'] in ['actor', 'writer']:
                    if not row['full_name'] in self.target[id][f'{row["role"]}s_names']:
                        self.target[id][f'{row["role"]}s_names'] += (row['full_name'] + ',')
                        self.target[id][f'{row["role"]}s'].append({
                            'id': str(row['pid']),
                            'name': row['full_name']
                        })
                if not row['gname'] in self.target[id]['genre']:
                    self.target[id]['genre'].append(row['gname'])
