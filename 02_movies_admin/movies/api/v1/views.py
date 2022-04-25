
from django.contrib.postgres.aggregates import ArrayAgg
from django.http import JsonResponse
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView

from movies.models import Filmwork


class MoviesApiMixin:
    model = Filmwork
    http_method_names = ['get']

    def get_queryset(self):
        # Return films, annotaed with actors/genres
        return Filmwork.objects.annotate(
            genre=ArrayAgg('genres__name',distinct = True),
            personnel=ArrayAgg('persons__id',distinct = True)
        ).values()

    def render_to_response(self, context, **response_kwargs):
        return JsonResponse(context)
    
    def api_schema_from_db_object(self, object):
        movie = object

        del movie['created_at']
        del movie['updated_at']
        movie['genres'] = movie['genre']
        del movie['genre']
        del movie['file_path']
        
        return movie


class MoviesListApi(MoviesApiMixin, ListView):

    def get_context_data(self, **kwargs):
        paginator, page, queryset, is_paginated = self.paginate_queryset(
                list(self.get_queryset()), 50)

        prev = int(self.request.GET.get('page')) \
            if self.request.GET.get('page') else 1
        next = prev + 1 if prev + 1 < paginator.num_pages else None

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
