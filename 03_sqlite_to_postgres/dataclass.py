
import uuid
import math
import random

from dataclasses import dataclass, field
from datetime import datetime

from faker import Faker
from faker.providers import lorem, date_time

fake = Faker()
fake.add_provider(lorem)
fake.add_provider(date_time)
Faker.seed(0)


@dataclass
class FilmWork:
    # movie = FilmWork(title='movie', description='new movie', rating=0.0)
    # Обратите внимание: для каждого поля указан тип
    type: str
    title: str
    description: str
    creation_date: datetime
    created_at: datetime
    updated_at: datetime
    # Ещё один бонус: в dataclass вы можете определить значение по умолчанию
    rating: float = field(default=0.0)
    file_path: str = field(default='./')
    id: uuid.UUID = field(default_factory=uuid.uuid4)

    # Fixes for schema inconsistencies when importing
    def __post_init__(self):
        # Replace, if NULL provided from source
        self.creation_date = self.creation_date or \
            fake.date_between('-50y')
        self.file_path = self.file_path or './' + \
            self.title.replace(' ', '')
        # Replace description, if NULL provided from source
        self.description = self.description or fake.text(max_nb_chars=100)
        # Replace description, if NULL provided from source
        self.rating = self.rating or math.floor(random.random() * 1000 / 100)


@dataclass
class Genre:
    name: str
    description: str
    created_at: datetime
    updated_at: datetime
    id: uuid.UUID = field(default_factory=uuid.uuid4)

    # Fixes for schema inconsistencies when importing
    def __post_init__(self):
        # Replace description, if NULL provided from source
        self.description = self.description or fake.text(max_nb_chars=30)


@dataclass
class Person:
    full_name: str
    created_at: datetime
    updated_at: datetime
    gender: str = field(
        default_factory=lambda: random.choice(['male', 'female'])
    )
    id: uuid.UUID = field(default_factory=uuid.uuid4)


@dataclass
class GenreFilmWork:
    film_work_id: uuid.UUID
    genre_id: uuid.UUID
    id: uuid.UUID
    created_at: datetime


@dataclass
class PersonFilmWork:
    film_work_id: uuid.UUID
    person_id: uuid.UUID
    role: str
    id: uuid.UUID
    created_at: datetime
