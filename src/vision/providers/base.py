import abc


class RateLimitError(Exception):
    pass


class ProviderError(Exception):
    pass


class BaseVisionProvider(abc.ABC):

    @property
    @abc.abstractmethod
    def name(self) -> str:
        ...

    @abc.abstractmethod
    def is_available(self) -> bool:
        ...

    @abc.abstractmethod
    def analyze(self, image_b64: str, mime_type: str, prompt: str) -> str:
        ...
