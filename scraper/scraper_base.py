from abc import ABC, abstractmethod


class ResponseError(Exception):

    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self.url = kwargs.get('url')

    def __str__(self):
        s = super().__str__()
        return '[{}]{}'.format(int(self.url / 40), s)


class ProcessingError(Exception):

    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self.url = kwargs.get('url')

    def __str__(self):
        s = super().__str__()
        return '[{}]{}'.format(int(self.url / 40), s)


class BaseScraper(ABC):

    @abstractmethod
    def get_content(self, start: int, end: int, *args, **kwargs) -> list:
        pass
