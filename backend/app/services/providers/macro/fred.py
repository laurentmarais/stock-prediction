from urllib.parse import urlencode

import pandas as pd

from app.services.providers.macro.base import MacroDataProvider


class FredMacroDataProvider(MacroDataProvider):
    def get_series(self, series_name: str, start: str, end: str) -> pd.DataFrame:
        params = urlencode(
            {
                "id": series_name,
                "cosd": start,
                "coed": end,
            }
        )
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?{params}"
        series = pd.read_csv(url)
        series["DATE"] = pd.to_datetime(series["DATE"])
        return series.rename(columns={"DATE": "date", series_name: "value"})
