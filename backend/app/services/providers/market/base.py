from abc import ABC, abstractmethod

import pandas as pd


class MarketDataProvider(ABC):
    @abstractmethod
    def get_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        lookback: str | None,
        as_of: str | None,
    ) -> pd.DataFrame:
        raise NotImplementedError
