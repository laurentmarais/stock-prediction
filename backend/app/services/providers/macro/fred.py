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
        date_column = "observation_date" if "observation_date" in series.columns else "DATE" if "DATE" in series.columns else None
        if date_column is None or series_name not in series.columns:
            return pd.DataFrame(columns=["date", "value"])

        series[date_column] = pd.to_datetime(series[date_column], errors="coerce")
        series[series_name] = pd.to_numeric(series[series_name], errors="coerce")
        return series.rename(columns={date_column: "date", series_name: "value"})[["date", "value"]].dropna()
