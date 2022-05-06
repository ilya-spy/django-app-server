
import sys

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Runs specified sql script or insert records into Django backend'

    # args and corresponding methods to invoke with db manager
    arguments_map = {
        'film_work': 'make_film_work',
        'person': 'make_person',
        'script': 'run_sql_file',
        'cast': 'cast_person_film_work',
    }

    def add_arguments(self, parser):
        parser.add_argument(
            '--script', type=str,
            help='runs the sql file specified')
        parser.add_argument(
            '--person', type=int,
            help='inserts specified num of person')
        parser.add_argument(
            '--film_work', type=int,
            help='inserts specified num of film_work')
        parser.add_argument(
            '--cast', type=int,
            help='inserts specified num of person, film_work and cast roles')

    def handle(self, *args, **options):
        sys.path.append('../01_schema_design')
        import movies_database

        sys.path.append('../03_sqlite_to_postgres')
        import db


        # Установим соединение с БД используя контекстный менеджер with.
        # В конце блока автоматически закроется курсор (cursor.close())
        # и соединение (conn.close())
        with db.postgres_manager() as connection:
            manager = movies_database.MoviesDatabaseManager(
                connection,
            )
            for key, value in Command.arguments_map.items():
                if options[key]:
                    self.stdout.write(
                        self.style.SUCCESS(f'Django backend: importing {key}')
                    )
                    proc = getattr(manager, value)
                    proc(options[key])

                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Django backend: succesfully processed {key}'
                        )
                    )
