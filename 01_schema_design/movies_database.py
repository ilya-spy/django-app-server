
import random
import math
import uuid
import logging
import pprint

from contextlib import contextmanager
from datetime import datetime
from psycopg2.extras import execute_batch, DictCursor

from faker import Faker
from faker.providers import lorem, date_time


logger = logging.getLogger(__name__)


fake = Faker()
fake.add_provider(lorem)
fake.add_provider(date_time)
Faker.seed(random.random())


# The manager does not setup schema
# Schema and extension must be properly managed in db sql
class MoviesDatabaseManager:
    def __init__(self, postgres_conn, chunk_size=50):
        self.__chunk_size = chunk_size
        self.__now = datetime.utcnow()

        # Disable autocommit and manual control for speed-up
        self.__connection = postgres_conn
        self.__connection.autocommit = False
        self.__cursor = postgres_conn.cursor()

        # Store managed records
        # only rows created through this manager could be managed
        self.__person_id = []
        self.__film_work_id = []

    def run_sql_file(self, filename):
        try:
            with open(filename, 'r') as sql_file:
                sql = sql_file.read()
                logger.info(f'Running SQL:\n{sql}')

                self.__cursor.execute(sql)
                self.__connection.commit()
        except IOError:
            logger.error(f'Error: can not read {filename}')

    def make_person(self, num_person):
        # Заполнение таблицы person
        ids = [uuid.uuid4() for _ in range(num_person)]
        query = 'INSERT INTO person (id, full_name, created, modified) \
                VALUES (%s, %s, %s, %s)'
        data = [
            (
                str(pk),
                fake.first_name() + ' ' + fake.last_name(),
                'now()', 'now()'
            ) for pk in ids
        ]
        execute_batch(self.__cursor, query, data, page_size=self.__chunk_size)
        self.__connection.commit()
        self.__person_id += ids
        logger.info('Inserted person:')
        logger.info(pprint.pformat(data, indent=2))

    def make_film_work(self, num_film_work):
        # Заполнение таблицы film_work
        ids = [uuid.uuid4() for _ in range(num_film_work)]
        query = 'INSERT INTO film_work \
            (id, title, description, creation_date, rating, type, created, modified) \
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)'
        data = [
            (
                str(pk),
                fake.text(max_nb_chars=30), fake.text(max_nb_chars=100),
                fake.date(),
                math.floor(random.random() * 100),
                random.choice(['movie', 'tv_show']), 'now()', 'now()'
            ) for pk in ids
        ]
        execute_batch(self.__cursor, query, data, page_size=self.__chunk_size)
        self.__connection.commit()
        self.__film_work_id += ids
        logger.info('Inserted film_work:')
        logger.info(pprint.pformat(data, indent=2))

    def cast_person_film_work(self, num_cast):
        # Заполнение таблицы PersonFilmWork
        person_film_work_data = []
        roles = ['actor', 'producer', 'director']

        # Make sure we generated enough staff to cast
        self.make_person(num_cast)
        self.make_film_work(num_cast)

        for _ in range(num_cast):
            # Select one of managed records to meet consistency requirements
            film_work_id = random.choice(self.__film_work_id)
            person_id = random.choice(self.__person_id)
            role = random.choice(roles)

            person_film_work_data.append((str(uuid.uuid4()), str(film_work_id),
                                          str(person_id), role, 'now()'))

        query = 'INSERT INTO person_film_work (id, film_work_id, person_id, role, created) \
            VALUES (%s, %s, %s, %s, %s)'
        logger.info('Cast roles:')
        logger.info(pprint.pformat(person_film_work_data, indent=2))

        execute_batch(self.__cursor, query, person_film_work_data, page_size=self.__chunk_size)
        self.__connection.commit()
