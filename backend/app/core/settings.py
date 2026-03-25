from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    market_data_provider: str = os.getenv("MARKET_DATA_PROVIDER", "yahoo")
    fundamentals_provider: str = os.getenv("FUNDAMENTALS_PROVIDER", "yahoo")
    macro_data_provider: str = os.getenv("MACRO_DATA_PROVIDER", "fred")
    event_data_provider: str = os.getenv("EVENT_DATA_PROVIDER", "public")


settings = Settings()
