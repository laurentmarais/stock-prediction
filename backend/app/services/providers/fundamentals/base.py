from abc import ABC, abstractmethod


class FundamentalsProvider(ABC):
    @abstractmethod
    def get_snapshot(self, symbol: str, as_of: str | None = None) -> dict:
        raise NotImplementedError
