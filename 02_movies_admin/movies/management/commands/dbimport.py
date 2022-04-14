
import sys
import time

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Imports the embedded SQLite database to Django backend'

    def add_arguments(self, parser):
        parser.add_argument(
            '--sqlite', type=str, required=True,
            help='imports specified SQLite db contents into Django backend'
        )

    def handle(self, *args, **options):
        sys.path.append('../03_sqlite_to_postgres')

        import db
        from dataclass import FilmWork, Person, Genre
        from dataclass import GenreFilmWork, PersonFilmWork

        # Установим соединение с БД используя контекстный менеджер with.
        # В конце блока автоматически закроется курсор (cursor.close())
        # и соединение (conn.close())
        with db.sqlite_manager(options['sqlite']) as sqlt:
            with db.postgres_manager() as psg:
                loader = db.SQLiteLoader(sqlt)
                saver = db.PostgresSaver(psg)

                # tables to process and corresponding dataclasses
                table_map = {
                    'film_work': FilmWork,
                    'person': Person,
                    'genre': Genre,
                    'genre_film_work': GenreFilmWork,
                    'person_film_work': PersonFilmWork,
                }

                start_time = time.time()
                for key, value in table_map.items():
                    # Import from SQLite into runtime dataclass
                    self.stdout.write(
                        self.style.SUCCESS(f'SQLite: loading {key}')
                    )
                    # Get generator cursor for source table rows
                    rows_producer = loader.fetch_table(key, value)
                    self.stdout.write(
                        self.style.SUCCESS(f'Postgres: saving {key}')
                    )
                    # Yield chunks from generator to avoid memory overloads
                    saver.insert_table(key, rows_producer, value)
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Succesfully inserted \
                                {loader.len_table(key)} records'
                        )
                    )
                self.stdout.write(
                    self.style.SUCCESS(f'--- {time.time() - start_time} seconds ---')
                )
