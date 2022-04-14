
from django.contrib import admin
from django.db.models import Prefetch
from django.utils.translation import gettext_lazy as _

# Register models here.
from .models import Genre
from .models import Filmwork
from .models import Person
from .models import GenreFilmwork
from .models import PersonFilmwork


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    # Отображение полей в списке
    list_display = ('full_name', 'gender',)
    search_fields = ('full_name', 'gender',)


class GenreInline(admin.TabularInline):
    model = GenreFilmwork
    verbose_name = _("genre_used_in")
    verbose_name_plural = _("genre_used_in_plural")

    list_prefetch_related = (Prefetch('genre'), Prefetch('film_work'))

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related(
            *self.list_prefetch_related
        ).all()

@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    inlines = (GenreInline,)

    # Отображение полей в списке
    list_display = ('name', 'description',)


class GenreFilmworkInline(admin.TabularInline):
    model = GenreFilmwork
    verbose_name = _("genre_film_work")
    verbose_name_plural = _("genre_film_work_plural")

    list_prefetch_related = (Prefetch('film_work'), Prefetch('genre'))

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related(
            *self.list_prefetch_related
        ).all()


class PersonFilmworkInline(admin.TabularInline):
    model = PersonFilmwork
    verbose_name = _("role_person_film_work")
    verbose_name_plural = _("role_person_film_work_plural")

    autocomplete_fields = ['person']
    list_prefetch_related = (Prefetch('film_work'), Prefetch('person'))

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related(
            *self.list_prefetch_related
        ).all()


@admin.register(Filmwork)
class FilmworkAdmin(admin.ModelAdmin):
    inlines = (PersonFilmworkInline, GenreFilmworkInline)

    # Отображение полей в списке
    list_display = ('title', 'description', 'type', 'creation_date', 'rating',)

    # Фильтрация в списке
    list_filter = ('type',)
    list_prefetch_related = (Prefetch('genres'), Prefetch('persons'))

    # Поиск по полям
    search_fields = ('title', 'description', 'id')

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related(
            *self.list_prefetch_related
        ).all()
