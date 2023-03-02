from pydantic import BaseModel
from typing import List, Optional


class BaseClass(BaseModel):
    id: str


class Person(BaseClass):
    name: str


class FilmWork(BaseClass):
    imdb_rating: Optional[float]
    title: str
    genre: List[str]
    description: Optional[str]
    director: List[str]
    actors_names: List[str]
    writers_names: List[str]
    actors: List[Person]
    writers: List[Person]
