
import factory
import random

from django.contrib.auth.models import User
from movies.models import Person, Genre, Filmwork, GenreFilmwork, PersonFilmwork



# Django core entities
class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Faker('user_name')
    email = factory.Faker('email')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')



# Application base entities
class PersonFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Person

    full_name = factory.Faker('name')
    gender = random.choice(['male', 'female'])


class GenreFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Genre

    name = factory.Faker('text', max_nb_chars=10).split(' ')[0]
    description = factory.Faker('text', max_nb_chars=30)


class FilmworkFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Filmwork

    title = factory.Faker('text', max_nb_chars=30)
    description = factory.Faker('text', max_nb_chars=120)
    
    creation_date = factory.Faker('date_between', start_date = '-50y')
    rating = factory.Faker('pyfloat', left_digits=2, right_digits=1, positive=True)
    file_path = factory.Faker('file_path', extension='mkv')

    type = random.choice(['movie', 'movie', 'tv_show'])



# Application entitites relation
class GenreFilmworkFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = GenreFilmwork

    genre = factory.SubFactory(GenreFactory)
    film_work = factory.SubFactory(FilmworkFactory)


class PersonFilmworkFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PersonFilmwork

    person = factory.SubFactory(PersonFactory)
    film_work = factory.SubFactory(FilmworkFactory)

    role = random.choice(
        ['actor' ] * 3 + ['producer', 'writer', 'director', 'operator', 'composer']
    )


# Filmwork with pre-filled genres and persons from related tables
class ActingFilmworkFactory(FilmworkFactory):
    genres = factory.RelatedFactory(
        GenreFilmworkFactory,
        factory_related_name='genre'
    )
    persons = factory.RelatedFactory(
        PersonFilmworkFactory,
        factory_related_name='person'
    )
