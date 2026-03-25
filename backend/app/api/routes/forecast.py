from fastapi import APIRouter, HTTPException, Query

from app.services.forecast_service import ForecastService
from app.services.provider_registry import get_market_provider


router = APIRouter(tags=["forecast"])
forecast_service = ForecastService()


@router.get("/forecast")
def get_forecast(
    symbol: str = Query(..., min_length=1),
    timeframe: str = Query("1d"),
    horizon_bars: int = Query(20, ge=5, le=250),
    as_of: str | None = Query(None),
):
    frame = get_market_provider().get_ohlcv(symbol, timeframe, None, as_of)
    if frame.empty:
        raise HTTPException(status_code=404, detail=f"No chart data returned for {symbol}")

    try:
        return forecast_service.build_forecast(symbol.upper(), timeframe, frame, horizon_bars)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
