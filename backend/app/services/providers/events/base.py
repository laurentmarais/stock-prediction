from abc import ABC, abstractmethod


class EventsProvider(ABC):
    @abstractmethod
    def get_events(self, symbol: str, as_of: str | None = None) -> dict:
        raise NotImplementedError
