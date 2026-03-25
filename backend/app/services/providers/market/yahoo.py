import pandas as pd
import yfinance as yf

from app.services.providers.market.base import MarketDataProvider


class YahooMarketDataProvider(MarketDataProvider):
    PERIOD_BY_TIMEFRAME = {
        "1m": "7d",
        "5m": "30d",
        "15m": "60d",
        "30m": "60d",
        "1h": "730d",
        "4h": "730d",
        "1d": "5y",
        "1wk": "10y",
        "1mo": "20y",
    }

    INTERVAL_MAP = {
        "1m": "1m",
        "5m": "5m",
        "15m": "15m",
        "30m": "30m",
        "1h": "60m",
        "4h": "1d",
        "1d": "1d",
        "1wk": "1wk",
        "1mo": "1mo",
    }

    def get_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        lookback: str | None,
        as_of: str | None,
    ) -> pd.DataFrame:
        period = lookback or self.PERIOD_BY_TIMEFRAME.get(timeframe, "1y")
        interval = self.INTERVAL_MAP.get(timeframe, "1d")
        frame = yf.download(symbol, period=period, interval=interval, auto_adjust=True, progress=False)
        if frame.empty:
            return frame

        if timeframe == "4h":
            frame = frame.resample("4h").agg(
                {
                    "Open": "first",
                    "High": "max",
                    "Low": "min",
                    "Close": "last",
                    "Volume": "sum",
                }
            ).dropna()

        frame = frame.reset_index()
        frame = self._normalize_columns(frame)
        if as_of is not None:
            anchor = pd.Timestamp(as_of)
            frame = frame[frame.iloc[:, 0] <= anchor]
        return frame

    def _normalize_columns(self, frame: pd.DataFrame) -> pd.DataFrame:
        if isinstance(frame.columns, pd.MultiIndex):
            frame.columns = [level_0 for level_0, _level_1 in frame.columns]
        return frame
