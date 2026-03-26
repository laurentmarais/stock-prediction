from fastapi import APIRouter, HTTPException, Query

from app.schemas.value_line import ValueLineResponse
from app.services.provider_registry import get_market_provider
from app.services.value_line_service import ValueLineService


router = APIRouter(tags=["value-line"])
value_line_service = ValueLineService()


@router.get("/value-line", response_model=ValueLineResponse)
def get_value_line(
    symbol: str = Query(..., min_length=1),
    timeframe: str = Query("1d"),
    lookback: str | None = Query(None),
    as_of: str | None = Query(None),
) -> ValueLineResponse:
    frame = get_market_provider().get_ohlcv(symbol, timeframe, lookback, as_of)
    if frame.empty:
        raise HTTPException(status_code=404, detail=f"No chart data returned for {symbol}")

    try:
        return value_line_service.build_value_line(symbol.upper(), timeframe, frame)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
