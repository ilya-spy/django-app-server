
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _

import uuid

#
# Описание миксинов
#


class CreatedAtMixin(models.Model):
    # auto_now_add автоматически выставит дату создания записи
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Указывает Django, что класс не является представлением таблицы
        abstract = True


class UpdatedAtMixin(models.Model):
    # auto_now изменятся при каждом обновлении записи
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Указывает Django, что класс не является представлением таблицы
        abstract = True


class UUIDMixin(models.Model):
    # Вам же придётся явно объявить primary key.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True

#
# Описание базовых сущностей
#


class Person(UUIDMixin, CreatedAtMixin, UpdatedAtMixin):

    class Gender(models.TextChoices):
        MALE = 'male', _('male')
        FEMALE = 'female', _('female')

    def __str__(self):
        return self.full_name

    full_name = models.CharField(_('full_name'), max_length=255)
    gender = models.TextField(_('gender'), choices=Gender.choices, null=True)

    class Meta:
        # Ваши таблицы находятся в нестандартной схеме.
        db_table = "content\".\"person"
        # Следующие два поля отвечают за название модели в интерфейсе
        verbose_name = 'Персона'
        verbose_name_plural = 'Персоны'


class Genre(UUIDMixin, CreatedAtMixin, UpdatedAtMixin):

    def __str__(self):
        return self.name

    # Первым аргументом обычно идёт человекочитаемое название поля
    name = models.CharField(_('name'), max_length=255)
    # blank=True делает поле необязательным для заполнения.
    description = models.TextField(_('description'), blank=True)

    class Meta:
        # Ваши таблицы находятся в нестандартной схеме.
        db_table = "content\".\"genre"
        # Следующие два поля отвечают за название модели в интерфейсе
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'


class Filmwork(UUIDMixin, CreatedAtMixin, UpdatedAtMixin):

    class FilmworkType(models.TextChoices):
        TV_SHOW = 'tv_show', _('tv_show')
        MOVIE = 'movie', _('movie_show')

    def __str__(self):
        return self.title

    # Первым аргументом обычно идёт человекочитаемое название поля
    title = models.CharField(_('title'), max_length=255)
    # blank=True делает поле необязательным для заполнения.
    description = models.TextField(_('description'), blank=True)

    creation_date = models.DateField(_('premiered'))
    rating = models.FloatField(_('rating'), blank=True,
                               validators=[MinValueValidator(0),
                                           MaxValueValidator(100)])
    type = models.TextField(_('type'), choices=FilmworkType.choices)

    # Параметр upload_to указывает, где будут храниться загружемые файлы
    # Базовая папка указана в файле настроек как MEDIA_ROOT
    file_path = models.FileField(_('file'), blank=True, null=True,
                                 upload_to='movies/')

    genres = models.ManyToManyField(Genre, through='GenreFilmwork')
    persons = models.ManyToManyField(Person, through='PersonFilmwork')

    class Meta:
        # Ваши таблицы находятся в нестандартной схеме.
        db_table = "content\".\"film_work"
        # Следующие два поля отвечают за название модели в интерфейсе
        verbose_name = 'Кинопроизведение'
        verbose_name_plural = 'Кинопроизведения'


#
# Oписание отношений между базовыми сущностями
#

class GenreFilmwork(UUIDMixin, CreatedAtMixin):

    def __str__(self):
        return str(self.id)

    film_work = models.ForeignKey('Filmwork', on_delete=models.CASCADE)
    genre = models.ForeignKey('Genre', on_delete=models.CASCADE)

    class Meta:
        db_table = "content\".\"genre_film_work"


class PersonFilmwork(UUIDMixin, CreatedAtMixin):

    def __str__(self):
        return self.role

    film_work = models.ForeignKey('filmwork', on_delete=models.CASCADE)
    person = models.ForeignKey('person', on_delete=models.CASCADE)

    role = models.CharField(_('role'), max_length=255, null=True)

    class Meta:
        db_table = "content\".\"person_film_work"
