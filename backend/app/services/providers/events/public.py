import yfinance as yf

from app.services.providers.events.base import EventsProvider


class PublicEventsProvider(EventsProvider):
    def get_events(self, symbol: str, as_of: str | None = None) -> dict:
        ticker = yf.Ticker(symbol)
        calendar = ticker.calendar
        if isinstance(calendar, dict):
            return {"as_of": as_of, **calendar}
        if getattr(calendar, "empty", True):
            return {"as_of": as_of}
        return {"as_of": as_of, **calendar.to_dict()}
