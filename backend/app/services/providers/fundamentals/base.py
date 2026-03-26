from abc import ABC, abstractmethod

import pandas as pd


class FundamentalsProvider(ABC):
    @abstractmethod
    def get_snapshot(self, symbol: str, as_of: str | None = None) -> dict:
        raise NotImplementedError

    @abstractmethod
    def get_time_series(self, symbol: str) -> dict[str, pd.Series]:
        raise NotImplementedError
