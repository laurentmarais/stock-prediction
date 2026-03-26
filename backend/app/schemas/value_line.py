from datetime import datetime

from pydantic import BaseModel


class ValueLinePoint(BaseModel):
    time: datetime
    fair_value: float


class ValueComponentSummary(BaseModel):
    name: str
    fair_value: float | None = None


class ValueLineSummary(BaseModel):
    fair_value: float | None = None
    upside_pct: float | None = None
    price_vs_value_pct: float | None = None
    active_models: int = 0
    signal: str = "unavailable"


class ValueLineResponse(BaseModel):
    symbol: str
    timeframe: str
    anchor_time: datetime
    current_price: float
    lookback_bars: int
    points: list[ValueLinePoint]
    summary: ValueLineSummary
    components: list[ValueComponentSummary]
