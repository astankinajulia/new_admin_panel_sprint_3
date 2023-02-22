from django.contrib import admin

from .models import Filmwork, Genre, GenreFilmwork, Person, PersonFilmwork


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name', 'created', 'modified')
    search_fields = ('name', 'description', 'id')


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'created', 'modified')
    search_fields = ('full_name', 'id')


class GenreFilmworkInline(admin.TabularInline):
    autocomplete_fields = ['genre']
    model = GenreFilmwork


class PersonFilmworkInline(admin.TabularInline):
    autocomplete_fields = ['person']
    model = PersonFilmwork


@admin.register(Filmwork)
class FilmworkAdmin(admin.ModelAdmin):
    inlines = (GenreFilmworkInline, PersonFilmworkInline)
    list_display = ('title', 'film_type', 'creation_date', 'rating', 'created', 'modified')
    list_filter = ('film_type', 'genres')
    search_fields = ('title', 'description', 'id')
