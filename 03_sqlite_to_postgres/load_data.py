import sqlite3
import json, uuid
from contextlib import contextmanager
from dataclasses import dataclass, field

import psycopg2
from psycopg2.extensions import connection as _connection
from psycopg2.extras import DictCursor


@contextmanager
def conn_context(db_path: str):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    yield conn # С конструкцией yield вы познакомитесь в следующем модуле 
    # Пока воспринимайте её как return, после которого код может продолжить выполняться дальше
    conn.close()


@dataclass
class FilmWork:
    # Обратите внимание: для каждого поля указан тип
    title: str
    description: str
    # Ещё один бонус: в dataclass вы можете определить значение по умолчанию
    rating: float = field(default=0.0)
    id: uuid.UUID = field(default_factory=uuid.uuid4)



movie = Movie(title='movie', description='new movie', rating=0.0)
print(movie)
# Movie(title='movie', description='new movie', rating=0.0, id=UUID('6fe77164-1dfe-470d-a32d-071973759539')) 

def save_film_work_to_postgres(conn: _connection, film_work: FilmWork):
    pass


def load_from_sqlite(connection: sqlite3.Connection, pg_conn: _connection):
    """Основной метод загрузки данных из SQLite в Postgres"""
    # postgres_saver = PostgresSaver(pg_conn)
    # sqlite_loader = SQLiteLoader(connection)

    # data = sqlite_loader.load_movies()
    # postgres_saver.save_all_data(data)


if __name__ == '__main__':
    dsl = {
        'dbname': 'movies_database',
        'user': 'app',
        'password': '123qwe', 
        'host': '127.0.0.1', 
        'port': 5432
    }
    with sqlite3.connect('db.sqlite') as sqlite_conn, psycopg2.connect(**dsl, cursor_factory=DictCursor) as pg_conn:
        load_from_sqlite(sqlite_conn, pg_conn)

    # Задаём путь к файлу с базой данных
    db_path = 'db.sqlite'

    with conn_context(db_path) as conn:
        curs = conn.cursor()
        curs.execute("SELECT * FROM film_work;")
        data = curs.fetchall()

        # Рассматриваем запись
        print(json.dumps(dict(data[3]), indent=2))
