
from django.contrib.postgres.aggregates import ArrayAgg
from django.http import JsonResponse
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.db.models import Q

from movies.models import Filmwork


class MoviesApiMixin:
    model = Filmwork
    http_method_names = ['get']

    def get_queryset(self):
        # Return films, annotaed with actors/genres
        return Filmwork.objects.annotate(
            genre=ArrayAgg('genres__name',distinct = True),
            actors=ArrayAgg(
                'persons__full_name',
                filter=Q(personfilmwork__role='actor'),
                distinct = True),
            directors=ArrayAgg(
                'persons__full_name',
                filter=Q(personfilmwork__role='director'),
                distinct = True),
            writers=ArrayAgg(
                'persons__full_name',
                filter=Q(personfilmwork__role='writer'),
                distinct = True)
        ).values()

    def render_to_response(self, context, **response_kwargs):
        return JsonResponse(context)
    
    def api_schema_from_db_object(self, object):
        movie = object

        del movie['created_at']
        del movie['updated_at']
        movie['genres'] = list(filter(lambda g: g, movie['genre']))
        del movie['genre']
        del movie['file_path']
        
        return movie


class MoviesListApi(MoviesApiMixin, ListView):

    def get_context_data(self, **kwargs):
        paginator, page, queryset, is_paginated = self.paginate_queryset(
                list(self.get_queryset()), 50)

        try:
            page = int(self.request.GET.get('page'))
        except:
            page = paginator.num_pages \
                if self.request.GET.get('page') == 'last' else 1

        prev = page - 1 if page > 1 else None
        next = page + 1 if page < paginator.num_pages else None

        context = {
            'count':  paginator.count,
            'total_pages': paginator.num_pages,
            'prev': prev,
            'next': next,
            'results': [self.api_schema_from_db_object(o) for o in queryset],
        }
        return context


class MoviesDetailApi(MoviesApiMixin, DetailView):

    def get_context_data(self, **kwargs):
        return self.api_schema_from_db_object(self.object)
