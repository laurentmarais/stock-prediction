from fastapi import APIRouter, HTTPException, Query

from app.schemas.market import OHLCVBar
from app.services.provider_registry import get_market_provider


router = APIRouter(tags=["chart"])


@router.get("/chart", response_model=list[OHLCVBar])
def get_chart_data(
    symbol: str = Query(..., min_length=1),
    timeframe: str = Query("1d"),
    lookback: str | None = Query(None),
    as_of: str | None = Query(None),
) -> list[OHLCVBar]:
    frame = get_market_provider().get_ohlcv(symbol, timeframe, lookback, as_of)
    if frame.empty:
        raise HTTPException(status_code=404, detail=f"No chart data returned for {symbol}")

    time_col = frame.columns[0]
    return [
        OHLCVBar(
            time=row[time_col],
            open=float(row.get("Open")),
            high=float(row.get("High")),
            low=float(row.get("Low")),
            close=float(row.get("Close")),
            volume=float(row.get("Volume")),
        )
        for _, row in frame.iterrows()
    ]
