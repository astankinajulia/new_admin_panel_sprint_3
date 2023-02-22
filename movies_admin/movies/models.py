import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import UniqueConstraint
from django.utils.translation import gettext_lazy as _


class TimeStampedMixin(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UUIDMixin(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class Genre(UUIDMixin, TimeStampedMixin):
    name = models.CharField(_('name'), max_length=255)
    description = models.TextField(_('description'), blank=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "content\".\"genre"
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'
        indexes = [
            models.Index(fields=['name'], name='name_idx'),
        ]


class Person(UUIDMixin, TimeStampedMixin):
    full_name = models.CharField(_('full name'), max_length=255)

    def __str__(self):
        return self.full_name

    class Meta:
        db_table = "content\".\"person"
        verbose_name = 'Человек'
        verbose_name_plural = 'Люди'
        indexes = [
            models.Index(fields=['full_name'], name='full_name_idx'),
        ]


class FilmType(models.TextChoices):
    MOVIE = 'MV', _('movie')
    TV_SHOW = 'TS', _('tv_show')


class Filmwork(UUIDMixin, TimeStampedMixin):
    title = models.CharField(_('title'), max_length=255)
    description = models.TextField(_('description'), blank=True)
    creation_date = models.DateField(_('release date'))
    rating = models.FloatField(
        _('rating'),
        blank=True,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100)
        ],
    )
    film_type = models.CharField(_('type'), max_length=2, choices=FilmType.choices, db_column='type')
    file_path = models.CharField(max_length=100, blank=True, null=True)
    genres = models.ManyToManyField(Genre, through='GenreFilmwork', verbose_name=_('genres'))
    persons = models.ManyToManyField(Person, through='PersonFilmwork', verbose_name=_('persons'))

    def __str__(self):
        return self.title

    class Meta:
        db_table = "content\".\"film_work"
        verbose_name = 'Фильм'
        verbose_name_plural = 'Фильмы'
        indexes = [
            models.Index(fields=['title'], name='title_idx'),
            models.Index(fields=['creation_date'], name='creation_date_idx'),
        ]


class GenreFilmwork(UUIDMixin):
    film_work = models.ForeignKey(Filmwork, on_delete=models.CASCADE)
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.film_work} - {self.genre}'

    class Meta:
        db_table = "content\".\"genre_film_work"
        verbose_name = 'Жанр фильма'
        verbose_name_plural = 'Жанры фильмов'

        constraints = [
            UniqueConstraint(
                fields=['film_work', 'genre'],
                name='film_work_genre_idx',
            ),
        ]


class Roles(models.TextChoices):
    ACTOR = 'actor', _('actor')
    DIRECTOR = 'director', _('director')
    WRITER = 'writer', _('writer')


class PersonFilmwork(UUIDMixin):
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    film_work = models.ForeignKey(Filmwork, on_delete=models.CASCADE)
    role = models.CharField(_('role'), max_length=255, null=False, choices=Roles.choices)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "content\".\"person_film_work"
        verbose_name = 'Человек и фильм'
        verbose_name_plural = 'Люди в фильмах'

        constraints = [
            UniqueConstraint(
                fields=['film_work_id', 'person_id', 'role'],
                name='film_work_person_role_idx',
            ),
        ]
