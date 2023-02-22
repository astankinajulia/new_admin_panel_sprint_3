from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import CharField, Q
from django.db.models.functions import Cast
from django.http import JsonResponse
from django.views.generic.detail import BaseDetailView
from django.views.generic.list import BaseListView

from movies.models import Filmwork, Roles


class MoviesApiMixin:
    model = Filmwork
    http_method_names = ['get']

    def get_queryset(self):
        movies = self.model.objects.all().prefetch_related('persons', 'genres', 'personfilmwork')
        return (
            movies
            .values(
                'id',
                'title',
                'description',
                'creation_date',
                'rating',
            )
            .annotate(
                type=Cast('film_type', output_field=CharField()),
                genres=ArrayAgg('genres__name', distinct=True),
                actors=ArrayAgg('persons__full_name', filter=Q(personfilmwork__role=Roles.ACTOR), distinct=True),
                directors=ArrayAgg('persons__full_name', filter=Q(personfilmwork__role=Roles.DIRECTOR), distinct=True),
                writers=ArrayAgg('persons__full_name', filter=Q(personfilmwork__role=Roles.WRITER), distinct=True),
            )
        )

    def render_to_response(self, context, **response_kwargs):
        return JsonResponse(context)


class MoviesListApi(MoviesApiMixin, BaseListView):
    paginate_by = 50

    def get_context_data(self, *, object_list=None, **kwargs):
        queryset = self.get_queryset()
        paginator, page, queryset, is_paginated = self.paginate_queryset(
            queryset,
            self.paginate_by,
        )

        page_number = self.request.GET.get('page')
        if page_number:
            if page_number.lower() == 'last':
                page_number = paginator.num_pages
            else:
                try:
                    page_number = int(page_number)
                except ValueError:
                    page_number = 1
        else:
            page_number = 1

        page_obj = paginator.get_page(page_number)

        return {
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'prev': page_obj.previous_page_number() if page_obj.has_previous() else None,
            'next': page_obj.next_page_number() if page_obj.has_next() else None,
            'results': list(page_obj),
        }


class MoviesDetailApi(MoviesApiMixin, BaseDetailView):
    pk_url_kwarg = 'id'

    def get_context_data(self, **kwargs):
        return super().get_object()
