from pydantic import BaseModel


class SymbolProfile(BaseModel):
    symbol: str
    requested_symbol: str
    company_name: str | None = None
    display_name: str | None = None
    exchange: str | None = None
    exchange_code: str | None = None
    quote_type: str | None = None
    sector: str | None = None
    industry: str | None = None
    matched_exact_symbol: bool = False
