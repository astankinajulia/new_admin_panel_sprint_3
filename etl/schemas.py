from __future__ import annotations

from pydantic import BaseModel


class BaseClass(BaseModel):
    id: str


class Person(BaseClass):
    name: str


class FilmWork(BaseClass):
    imdb_rating: float | None
    title: str
    genre: list[str]
    description: str | None
    director: list[str]
    actors_names: list[str]
    writers_names: list[str]
    actors: list[Person]
    writers: list[Person]
