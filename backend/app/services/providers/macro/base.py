from abc import ABC, abstractmethod

import pandas as pd


class MacroDataProvider(ABC):
    @abstractmethod
    def get_series(self, series_name: str, start: str, end: str) -> pd.DataFrame:
        raise NotImplementedError
