
from django.db import transaction
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from movies.factories import PersonFactory, GenreFactory, ActingFilmworkFactory
from movies.factories import PersonFilmworkFactory, GenreFilmworkFactory
from movies.models import Filmwork


class Command(BaseCommand):
    help = 'Populate instances of django models from factories'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count', type=int, required=True,
            help='Number of records to insert')
        parser.add_argument(
            '--make', type=str,
            help='Name of an instance to insert (person|genre|filmwork)')
        parser.add_argument(
            '--cast', type=str,
            help='Name of a relation to cast (person_filmwork|genre_filmwork)')

    # args and corresponding methods to invoke with db manager
    make_map = {
        'film_work': ActingFilmworkFactory,
        'person': PersonFactory,
        'genre': GenreFactory,
    }
    cast_map = {
        'person_filmwork': PersonFilmworkFactory,
        'genre_filmwork': GenreFilmworkFactory,
    }

    @transaction.atomic
    def handle(self, *args, **options):
        # demo-only example of django user management
        # User.objects.exclude(username='ilya').delete()

        # demo-only example of django app db management
        # Filmwork.objects.all().delete()
        pass

        if options['make'] in Command.make_map:
            objects = [
                Command.make_map[options['make']]
                for _ in range(options['count'])]
            self.stdout.write(
                self.style.SUCCESS('Django backend: inserting objects...')
            )
            for object in objects:
                object.build()
                self.stdout.write(
                        self.style.WARNING(
                            object.title
                        )
                    )

        if options['cast'] in Command.cast_map:
            relations = [Command.cast_map[options['cast']]
                         for _ in range(options['count'])]
            self.stdout.write(
                self.style.SUCCESS('Django backend: inserted relations')
            )
            for relation in relations:
                self.stdout.write(
                        self.style.WARNING(
                            f'{relation.film_work}'
                        )
                    )
