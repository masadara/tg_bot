from abc import ABC, abstractmethod
import requests


class AbstractHHAPI(ABC):
    '''Абстрактный класс для API'''
    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def get_vacancies(self, query):
        pass

    @abstractmethod
    def close_connection(self):
        pass

class HHAPI(AbstractHHAPI):
    '''Класс для API'''
    def __init__(self):
        self.url = "https://api.hh.ru/vacancies"
        self.session = None

    def connect(self):
        self.session = requests.Session()

    def get_vacancies(self, query):
        response = self.session.get(self.url, params={'text': query})
        return response.json().get('items', [])

    def close_connection(self):
        if self.session:
            self.session.close()