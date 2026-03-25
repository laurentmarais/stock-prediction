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
        }
