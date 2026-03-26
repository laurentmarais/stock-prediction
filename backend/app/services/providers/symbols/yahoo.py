import yfinance as yf

from app.schemas.symbols import SymbolProfile
from app.services.providers.symbols.base import SymbolLookupProvider


class YahooSymbolLookupProvider(SymbolLookupProvider):
    def get_profile(self, symbol: str) -> SymbolProfile:
        requested_symbol = symbol.strip().upper()
        profile = SymbolProfile(
            symbol=requested_symbol,
            requested_symbol=requested_symbol,
        )

        try:
            search = yf.Search(query=requested_symbol, max_results=10)
            exact_match = next(
                (
                    quote
                    for quote in search.quotes
                    if str(quote.get("symbol", "")).upper() == requested_symbol
                ),
                None,
            )
            if exact_match:
                profile = SymbolProfile(
                    symbol=str(exact_match.get("symbol", requested_symbol)).upper(),
                    requested_symbol=requested_symbol,
                    company_name=exact_match.get("longname") or exact_match.get("shortname"),
                    display_name=exact_match.get("shortname") or exact_match.get("longname"),
                    exchange=exact_match.get("exchDisp") or exact_match.get("exchange"),
                    exchange_code=exact_match.get("exchange"),
                    quote_type=exact_match.get("typeDisp") or exact_match.get("quoteType"),
                    sector=exact_match.get("sectorDisp") or exact_match.get("sector"),
                    industry=exact_match.get("industryDisp") or exact_match.get("industry"),
                    matched_exact_symbol=True,
                )
        except Exception:
            pass

        if not profile.matched_exact_symbol and not profile.company_name:
            return profile

        try:
            info = yf.Ticker(requested_symbol).info
        except Exception:
            info = {}

        return SymbolProfile(
            symbol=str(info.get("symbol") or profile.symbol or requested_symbol).upper(),
            requested_symbol=requested_symbol,
            company_name=profile.company_name or info.get("longName") or info.get("shortName"),
            display_name=profile.display_name or info.get("displayName") or info.get("shortName") or info.get("longName"),
            exchange=profile.exchange or info.get("fullExchangeName") or info.get("exchange"),
            exchange_code=profile.exchange_code or info.get("exchange"),
            quote_type=profile.quote_type or info.get("quoteType"),
            sector=profile.sector or info.get("sector"),
            industry=profile.industry or info.get("industry"),
            matched_exact_symbol=profile.matched_exact_symbol,
        )
