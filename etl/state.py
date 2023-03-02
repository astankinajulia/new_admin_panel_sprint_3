import abc
import json
import os
import redis as Redis
from typing import Any, Optional


class BaseStorage:
    @abc.abstractmethod
    def save_state(self, state: dict) -> None:
        """Сохранить состояние в постоянное хранилище"""
        pass

    @abc.abstractmethod
    def retrieve_state(self) -> dict:
        """Загрузить состояние локально из постоянного хранилища"""
        pass


class JsonFileStorage(BaseStorage):
    def __init__(self, file_path: Optional[str] = None):
        self.file_path = file_path
        self.is_file = os.path.isfile(self.file_path)

    def save_state(self, state: dict):
        if state:
            with open(self.file_path, "w") as file1:
                file1.write(json.dumps(state))

    def retrieve_state(self):
        if not self.is_file:
            return {}
        with open(self.file_path, "r") as file1:
            content = file1.read()
            if content:
                if type(json.loads(content)) == dict:
                    return json.loads(content)
                elif content == '':
                    return {}
            return {}


class RedisStorage(BaseStorage):

    def __init__(self, redis_adapter: Redis):
        self.redis_adapter = redis_adapter

    def save_state(self, state: dict):
        if state:
            self.redis_adapter.set('data', json.dumps(state))

    def retrieve_state(self):
        content = self.redis_adapter.get('data')
        if content:
            if type(json.loads(content)) == dict:
                return json.loads(content)
            elif content == '':
                return {}
        return {}


class State:
    """
    Класс для хранения состояния при работе с данными, чтобы постоянно не перечитывать данные с начала.
    Здесь представлена реализация с сохранением состояния в файл.
    В целом ничего не мешает поменять это поведение на работу с БД или распределённым хранилищем.
    """

    def __init__(self, storage: BaseStorage):
        self.storage = storage
        self.state = self.storage.retrieve_state()

    def set_state(self, key: str, value: Any) -> None:
        """Установить состояние для определённого ключа"""
        if key and value:
            if type(self.state) == dict:
                self.state[key] = value
                self.storage.save_state(self.state)
        self.state = self.storage.retrieve_state()

    def get_state(self, key: str) -> Any:
        """Получить состояние по определённому ключу"""
        self.state = self.storage.retrieve_state()
        if self.state and self.state.get(key):
            return self.state[key]
        return None
