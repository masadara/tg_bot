class Vacancy:
    '''Класс для вакансий'''
    def __init__(self, title, url, salary=None, description=''):
        self.title = title
        self.url = url
        self.salary = salary if salary is not None else 'Зарплата не указана'
        self.description = description

    def __lt__(self, other):
        return (self.salary if isinstance(self.salary, (int, float)) else 0) < (other.salary if isinstance(other.salary, (int, float)) else 0)

    def __repr__(self):
        return f'{self.title}, {self.salary}, {self.url}'