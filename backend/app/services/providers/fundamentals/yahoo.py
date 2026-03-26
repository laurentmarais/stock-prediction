from __future__ import annotations

import pandas as pd
import yfinance as yf

from app.services.providers.fundamentals.base import FundamentalsProvider


class YahooFundamentalsProvider(FundamentalsProvider):
    def get_snapshot(self, symbol: str, as_of: str | None = None) -> dict:
        info = yf.Ticker(symbol).info
        return {
            "symbol": symbol,
            "as_of": as_of,
            "market_cap": info.get("marketCap"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "profit_margin": info.get("profitMargins"),
            "operating_margin": info.get("operatingMargins"),
            "beta": info.get("beta"),
            "trailing_eps": info.get("trailingEps"),
            "total_revenue": info.get("totalRevenue"),
            "shares_outstanding": info.get("sharesOutstanding"),
            "book_value_per_share": info.get("bookValue"),
            "total_assets": info.get("totalAssets"),
            "total_liabilities": info.get("totalLiab"),
        }

    def get_time_series(self, symbol: str) -> dict[str, pd.Series]:
        ticker = yf.Ticker(symbol)
        quarterly_income = self._safe_frame(ticker.quarterly_income_stmt)
        annual_income = self._safe_frame(ticker.income_stmt)
        quarterly_balance = self._safe_frame(ticker.quarterly_balance_sheet)
        annual_balance = self._safe_frame(ticker.balance_sheet)

        return {
            "eps": self._first_non_empty(
                self._extract_series(quarterly_income, ["Diluted EPS", "Basic EPS"]),
                self._extract_series(annual_income, ["Diluted EPS", "Basic EPS"]),
            ),
            "revenue": self._first_non_empty(
                self._extract_series(quarterly_income, ["Total Revenue", "Operating Revenue"]),
                self._extract_series(annual_income, ["Total Revenue", "Operating Revenue"]),
            ),
            "shares": self._first_non_empty(
                self._extract_series(quarterly_balance, ["Ordinary Shares Number", "Share Issued"]),
                self._extract_series(quarterly_income, ["Diluted Average Shares", "Basic Average Shares"]),
                self._extract_series(annual_balance, ["Ordinary Shares Number", "Share Issued"]),
            ),
            "book_equity": self._first_non_empty(
                self._extract_series(quarterly_balance, ["Common Stock Equity", "Stockholders Equity", "Total Equity Gross Minority Interest"]),
                self._extract_series(annual_balance, ["Common Stock Equity", "Stockholders Equity", "Total Equity Gross Minority Interest"]),
            ),
            "total_assets": self._first_non_empty(
                self._extract_series(quarterly_balance, ["Total Assets"]),
                self._extract_series(annual_balance, ["Total Assets"]),
            ),
            "total_liabilities": self._first_non_empty(
                self._extract_series(quarterly_balance, ["Total Liabilities Net Minority Interest", "Total Liabilities"]),
                self._extract_series(annual_balance, ["Total Liabilities Net Minority Interest", "Total Liabilities"]),
            ),
        }

    def _safe_frame(self, frame: pd.DataFrame | None) -> pd.DataFrame:
        if frame is None or frame.empty:
            return pd.DataFrame()
        return frame

    def _extract_series(self, frame: pd.DataFrame, aliases: list[str]) -> pd.Series:
        if frame.empty:
            return pd.Series(dtype=float)
        for alias in aliases:
            if alias in frame.index:
                series = pd.to_numeric(frame.loc[alias], errors="coerce").dropna()
                series.index = pd.to_datetime(series.index)
                return series.sort_index()
        return pd.Series(dtype=float)

    def _first_non_empty(self, *series_list: pd.Series) -> pd.Series:
        for series in series_list:
            if series is not None and not series.empty:
                return series
        return pd.Series(dtype=float)
