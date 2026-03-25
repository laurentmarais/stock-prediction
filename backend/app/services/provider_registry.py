from app.core.settings import settings
from app.services.providers.base import ProviderInfo
from app.services.providers.events.public import PublicEventsProvider
from app.services.providers.fundamentals.yahoo import YahooFundamentalsProvider
from app.services.providers.macro.fred import FredMacroDataProvider
from app.services.providers.market.yahoo import YahooMarketDataProvider


MARKET_PROVIDERS = {
    "yahoo": YahooMarketDataProvider,
}

FUNDAMENTALS_PROVIDERS = {
    "yahoo": YahooFundamentalsProvider,
}

MACRO_PROVIDERS = {
    "fred": FredMacroDataProvider,
}

EVENT_PROVIDERS = {
    "public": PublicEventsProvider,
}


def get_market_provider():
    return MARKET_PROVIDERS[settings.market_data_provider]()


def get_fundamentals_provider():
    return FUNDAMENTALS_PROVIDERS[settings.fundamentals_provider]()


def get_macro_provider():
    return MACRO_PROVIDERS[settings.macro_data_provider]()


def get_events_provider():
    return EVENT_PROVIDERS[settings.event_data_provider]()


def get_provider_info() -> dict[str, ProviderInfo]:
    return {
        "market": ProviderInfo(settings.market_data_provider, sorted(MARKET_PROVIDERS.keys())),
        "fundamentals": ProviderInfo(settings.fundamentals_provider, sorted(FUNDAMENTALS_PROVIDERS.keys())),
        "macro": ProviderInfo(settings.macro_data_provider, sorted(MACRO_PROVIDERS.keys())),
        "events": ProviderInfo(settings.event_data_provider, sorted(EVENT_PROVIDERS.keys())),
    }