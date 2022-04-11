
from django.contrib import admin

# Register your models here.
from .models import Genre
from .models import Filmwork
from .models import Person
from .models import GenreFilmwork
from .models import PersonFilmwork


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    pass


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    # Отображение полей в списке
    list_display = ('full_name', 'gender',)


class GenreFilmworkInline(admin.TabularInline):
    model = GenreFilmwork


class PersonFilmworkInline(admin.TabularInline):
    model = PersonFilmwork


@admin.register(Filmwork)
class FilmworkAdmin(admin.ModelAdmin):
    inlines = (PersonFilmworkInline, GenreFilmworkInline)

    # Отображение полей в списке
    list_display = ('title', 'type', 'creation_date', 'rating',)

    # Фильтрация в списке
    list_filter = ('type',)

    # Поиск по полям
    search_fields = ('title', 'description', 'id')
