from elasticsearch import RequestsHttpConnection
from pydantic import BaseSettings, RedisDsn


class Settings(BaseSettings):
    timeout: int = 60

    redis_host: str
    redis_port: str

    postgres_db: str
    postgres_user: str
    postgres_password: str
    db_host: str
    db_port: str

    es_host: str
    es_port: str

    class Config:
        env_file = './config/.env'

    def get_es_settings(self) -> dict:
        return {
            'hosts': [
                {
                    'host': self.es_host,
                    'port': self.es_port,
                }
            ],
            'max_retries': 30,
            'retry_on_timeout': True,
            'request_timeout': 30,
            'connection_class': RequestsHttpConnection,
        }

    def get_pg_dsn(self) -> dict:
        return {
            'dbname': self.postgres_db,
            'user': self.postgres_user,
            'password': self.postgres_password,
            'host': self.db_host,
            'port': self.db_port,
            'options': '-c search_path=content',
        }

    def get_redis_settings(self) -> str:
        return RedisDsn.build(
            scheme='redis',
            host=self.redis_host,
            port=self.redis_port,
        )
