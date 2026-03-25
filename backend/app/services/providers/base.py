from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderInfo:
    selected: str
    available: list[str]
