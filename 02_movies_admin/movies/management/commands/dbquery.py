
import sys

from django.core.management.base import BaseCommand, CommandError
from movies.models import Person, Genre, Filmwork, GenreFilmwork, PersonFilmwork


class Command(BaseCommand):
    help = 'Runs specified sql script or insert records into Django backend'

    def add_arguments(self, parser):
        parser.add_argument('--script', type=str,
            help='runs the sql file specified')
        parser.add_argument('--person', type=int,
            help='inserts specified num of person')
        parser.add_argument('--film_work', type=int,
            help='inserts specified num of film_work')
        parser.add_argument('--cast', type=int,
            help='inserts specified num of person, film_work and cast roles')

    def handle(self, *args, **options):
        sys.path.append('../01_schema_design')
        import movies_database

        # Установим соединение с БД используя контекстный менеджер with.
        # В конце блока автоматически закроется курсор (cursor.close())
        # и соединение (conn.close())
        with movies_database.postgres_manager() as connection:
            manager = movies_database.MoviesDatabaseManager(
                connection,
            )
            if options['script']:
                manager.run_sql_file(options['script'])
            if options['person']:
                manager.make_person(options['person'])
            if options['film_work']:
                manager.make_film_work(options['film_work'])
            if options['cast']:
                manager.cast_person_film_work(options['cast'])
