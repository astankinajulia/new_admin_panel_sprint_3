import logging
import logging.config
from typing import Iterator

from psycopg2.extensions import connection as _connection
from pydantic import ValidationError

from schemas import FilmWork, Person

PACK_SIZE = 100


class DataTypes:
    FILMWORK = 'filmwork'
    GENRE = 'genre'
    PERSON = 'person'


class Roles:
    ACTOR = 'actor'
    DIRECTOR = 'director'
    WRITER = 'writer'


SQL_SELECT_PART = """
SELECT
fw.id,
fw.title,
fw.description,
fw.rating,
fw.type,
fw.created,
fw.modified,
COALESCE (
   json_agg(
       DISTINCT jsonb_build_object(
           'person_role', pfw.role,
           'person_id', p.id,
           'person_name', p.full_name
       )
   ) FILTER (WHERE p.id is not null),
   '[]'
) as persons,
array_agg(DISTINCT g.name) as genres
"""

FROM_FILMWORKS = 'FROM content.film_work fw'
FROM_GENRES = 'FROM content.genre g'
FROM_PERSONS = 'FROM content.person p'

JOIN_FOR_FILMWORKS = """
LEFT JOIN content.person_film_work pfw ON pfw.film_work_id = fw.id
LEFT JOIN content.person p ON p.id = pfw.person_id
LEFT JOIN content.genre_film_work gfw ON gfw.film_work_id = fw.id
LEFT JOIN content.genre g ON g.id = gfw.genre_id"""

JOIN_FOR_GENRES = """LEFT JOIN content.genre_film_work gfw ON gfw.genre_id = g.id
LEFT JOIN content.film_work fw ON fw.id = gfw.film_work_id
LEFT JOIN content.person_film_work pfw ON pfw.film_work_id = fw.id
LEFT JOIN content.person p ON p.id = pfw.person_id"""

JOIN_FOR_PERSONS = """LEFT JOIN content.person_film_work pfw ON pfw.person_id = p.id
LEFT JOIN content.film_work fw ON fw.id = pfw.film_work_id
LEFT JOIN content.genre_film_work gfw ON gfw.film_work_id = fw.id
LEFT JOIN content.genre g ON g.id = gfw.genre_id
"""

logging.config.fileConfig(fname='./config/logger.conf', disable_existing_loggers=False)
logger = logging.getLogger(__name__)


class PostgresExtractor:
    """ Чтение данных из postgreSQL пачками. """

    def __init__(self, connection: _connection, modified_time: str, pack_size: int = PACK_SIZE):
        self.pack_size = pack_size
        self.modified_time = modified_time

        self.connection = connection
        self.cursor = connection.cursor()

    def get_filmworks(self):
        """ Запрос на получение "модифицированных"  фильмов. """
        logger.info(f'Select filmworks, {self.modified_time}')
        self.cursor.execute(
            f'{SQL_SELECT_PART} {FROM_FILMWORKS} {JOIN_FOR_FILMWORKS}'
            f"WHERE fw.modified > '{self.modified_time}'"
            'GROUP BY fw.id, fw.modified'
            'ORDER BY fw.modified;'

        )

    def get_genres(self):
        """ Запрос на получение "модифицированных"  жанров. """
        logger.info(f'Select genres, {self.modified_time}')
        self.cursor.execute(
            f'{SQL_SELECT_PART} {FROM_GENRES} {JOIN_FOR_GENRES}'
            f"'WHERE g.modified > '{self.modified_time}'"
            'GROUP BY fw.id;'
        )

    def get_persons(self):
        """ Запрос на получение "модифицированных" людей. """
        logger.info(f'Select persons, {self.modified_time}')
        self.cursor.execute(
            f'{SQL_SELECT_PART} {FROM_PERSONS} {JOIN_FOR_PERSONS}'
            f"WHERE p.modified > '{self.modified_time}'"
            'GROUP BY fw.id;'
        )

    def _get_data(self, data_type: str):
        """
        Получить данные из БД
        :param data_type: тип данных, который менялся
        :return:
        """
        if data_type == DataTypes.FILMWORK:
            extractor = self.get_filmworks
        elif data_type == DataTypes.GENRE:
            extractor = self.get_genres
        elif data_type == DataTypes.PERSON:
            extractor = self.get_persons
        else:
            raise ValidationError
        try:
            extractor()
        except Exception as e:
            logger.error(f'Ошибка чтения {data_type}', exc_info=True)
            raise Exception(e)

        while True:
            rows = self.cursor.fetchmany(size=self.pack_size)
            if not rows:
                return
            yield from rows

    def get_film_data(self) -> Iterator:
        return self._get_data(DataTypes.FILMWORK)

    def get_genres_data(self) -> Iterator:
        return self._get_data(DataTypes.GENRE)

    def get_persons_data(self) -> Iterator:
        return self._get_data(DataTypes.PERSON)


class DataTransform:
    """ Преобразование данных из формата Postgres в формат, пригодный для Elasticsearch. """

    def __init__(self, etl_index_name):
        self.etl_index_name = etl_index_name

    @staticmethod
    def _transform(data: dict) -> FilmWork:
        """
        Преобразование данных, полученных из posgres в структуру для индекса etl
        :param data: данные для трансформации
        :return:
        """
        persons = data.get('persons')
        director = []
        actors_names = []
        writers_names = []
        actors = []
        writers = []
        for person in persons:
            if person.get('person_role') == Roles.ACTOR:
                actors_names.append(person.get('person_name'))
                actors.append(Person(id=person.get('person_id'), name=person.get('person_name')))
            elif person.get('person_role') == Roles.DIRECTOR:
                director.append(person.get('person_name'))
            elif person.get('person_role') == Roles.WRITER:
                writers_names.append(person.get('person_name'))
                writers.append(Person(id=person.get('person_id'), name=person.get('person_name')))

        return FilmWork(
            id=data.get('id'),
            imdb_rating=data.get('rating'),
            title=data.get('title'),
            genre=data.get('genres'),
            description=data.get('description'),
            director=director,
            actors_names=actors_names,
            writers_names=writers_names,
            actors=actors,
            writers=writers,
        )

    def transform_generator(self, postres_data: Iterator[dict]) -> Iterator[dict]:
        """
        Преобразование пачки данных из posgres в данные для загрузки в etl
        :param postres_data: итератор с данными из posgres
        :return:
        """
        for data in postres_data:
            result = self._transform(data).dict()
            result_id = result.get('id')
            yield {
                '_index': self.etl_index_name,
                '_op_type': 'update',
                'doc_as_upsert': True,
                '_id': result_id,
                'doc': result,
            }
