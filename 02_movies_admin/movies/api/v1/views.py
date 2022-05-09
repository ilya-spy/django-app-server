
from django.contrib.postgres.aggregates import ArrayAgg
from django.http import JsonResponse
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.db.models import Q

from movies.models import Filmwork

class MoviesApiMixin:
    model = Filmwork
    http_method_names = ['get']

    def _aggregate_person(self, role):
        return ArrayAgg('persons__full_name',
                        filter=Q(personfilmwork__role=role),
                        distinct=True)

    def get_queryset(self):
        # Return films, annotaed with actors/genres
        return Filmwork.objects.annotate(
            actors = self._aggregate_person('actor'),
            directors = self._aggregate_person('director'),
            writers=self._aggregate_person('writer')
        ).values(
            'id','title','description','creation_date',
            'rating','type','actors','writers','directors',
                  genre=ArrayAgg('genres__name',
                    filter=Q(genres__name__isnull=False),
                    distinct = True))

    def render_to_response(self, context, **response_kwargs):
        return JsonResponse(context)

class MoviesListApi(MoviesApiMixin, ListView):

    def get_context_data(self, **kwargs):
        paginator, page, queryset, is_paginated = self.paginate_queryset(
                list(self.get_queryset()), 50)

        page = paginator.get_page(self.request.GET.get('page'))
        prev = page.previous_page_number() if page.has_previous() else None
        next = page.next_page_number() if page.has_next() else None

        context = {
            'count':  paginator.count,
            'total_pages': paginator.num_pages,
            'prev': prev,
            'next': next,
            'results': queryset,
        }
        return context


class MoviesDetailApi(MoviesApiMixin, DetailView):

    def get_context_data(self, **kwargs):
        return kwargs['object']
