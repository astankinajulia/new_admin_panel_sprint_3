import contextlib
import datetime
import logging.config
from functools import lru_cache
from time import sleep

import backoff
import psycopg2
import redis
from elasticsearch import Elasticsearch

from elasticsearch.helpers import bulk
from psycopg2.extras import DictCursor

import config.settings as sett
from postgres import PostgresExtractor, DataTransform
from state import State, RedisStorage

PACK_SIZE = 100
ETL_INDEX_NAME = 'movies'
INIT_DATE = '1900-05-10 20:14:09.221958+00'

PostgresBaseError = (
    psycopg2.Error, psycopg2.Warning, psycopg2.DataError, psycopg2.DatabaseError, psycopg2.ProgrammingError,
    psycopg2.IntegrityError, psycopg2.InterfaceError, psycopg2.InternalError, psycopg2.NotSupportedError,
    psycopg2.OperationalError,
)


@lru_cache()
def get_settings() -> sett.Settings:
    return sett.Settings()


logging.config.fileConfig(fname='./config/logger.conf', disable_existing_loggers=False)
logger = logging.getLogger(__name__)


def now() -> str:
    return str(datetime.datetime.now().date())


@backoff.on_exception(backoff.expo, PostgresBaseError)
def postgres_connect(*args, **kwargs):
    return psycopg2.connect(*args, **kwargs)


@contextlib.contextmanager
def connection_postgres_context(*args, **kwargs):
    """ Контекстный менеджер для подключения к Posgresql. """
    logger.info('Start pg connection')
    connection = postgres_connect(*args, **kwargs)
    try:
        yield connection
    except Exception as error:
        logger.error(error, exc_info=True)
    finally:
        connection.close()


@backoff.on_exception(backoff.expo, Exception)
def es_connect(*args, **kwargs):
    return Elasticsearch(*args, **kwargs)


@contextlib.contextmanager
def es_connector(*args, **kwargs):
    """ Контекстный менеджер для подключения к ETL. """
    logger.info('Start es connection')
    connection = es_connect(*args, **kwargs)
    try:
        yield connection
    except Exception as error:
        logger.error(error, exc_info=True)
    finally:
        connection.close()


class ElasticsearchLoader:
    """ Забирает данные в подготовленном формате и загружает их в Elasticsearch"""

    def __init__(self, es_connectin):
        self.es = es_connectin

    def set_bulk_data_to_etl(self, bulk_data) -> None:
        """ Отправка данных в ETL. """
        bulk(self.es, bulk_data)
        logger.info('Data transferred to ES')


if __name__ == '__main__':
    settings: sett.Settings = get_settings()

    redis_connection = redis.StrictRedis.from_url(settings.get_redis_settings())
    redis = RedisStorage(redis_connection)
    state = State(redis)

    if not state.get_state('modified'):
        state.set_state('modified', INIT_DATE)

    with connection_postgres_context(
            **settings.get_pg_dsn(),
            cursor_factory=DictCursor,
    ) as pg_conn, pg_conn.cursor() as pg_curs, es_connector(**settings.get_es_settings()) as es_conn:
        es = ElasticsearchLoader(es_conn)
        data_transformer: DataTransform = DataTransform(ETL_INDEX_NAME)
        pg_extractor: PostgresExtractor = PostgresExtractor(pg_curs, state.get_state('modified'), PACK_SIZE)

        logger.info('Start ETL process')
        while True:
            try:
                es.set_bulk_data_to_etl(data_transformer.transform_generator(pg_extractor.get_film_data()))
                es.set_bulk_data_to_etl(data_transformer.transform_generator(pg_extractor.get_genres_data()))
                es.set_bulk_data_to_etl(data_transformer.transform_generator(pg_extractor.get_persons_data()))
            except Exception as exc:
                logger.error(exc, exc_info=True)
            state.set_state('modified', now())
            pg_extractor.modified_time = state.get_state('modified')
            logger.info('Wait')
            sleep(settings.timeout)
