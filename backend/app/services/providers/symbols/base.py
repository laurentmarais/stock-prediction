from abc import ABC, abstractmethod

from app.schemas.symbols import SymbolProfile


class SymbolLookupProvider(ABC):
    @abstractmethod
    def get_profile(self, symbol: str) -> SymbolProfile:
        raise NotImplementedError
