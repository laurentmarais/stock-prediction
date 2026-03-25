from datetime import datetime

from pydantic import BaseModel


class ScenarioCard(BaseModel):
    name: str
    probability: float
    description: str


class ForecastBandPoint(BaseModel):
    time: datetime
    p10: float
    p25: float
    p50: float
    p75: float
    p90: float


class RegimePoint(BaseModel):
    time: datetime
    regime: str


class ForecastResponse(BaseModel):
    symbol: str
    timeframe: str
    horizon_bars: int
    anchor_time: datetime
    regime_label: str
    regime_match_count: int
    current_price: float
    probability_up: float
    probability_down_5: float
    probability_up_5: float
    probability_down_10: float
    probability_up_10: float
    scenarios: list[ScenarioCard]
    forecast: list[ForecastBandPoint]
    regime_history: list[RegimePoint]
