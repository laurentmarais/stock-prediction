from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from app.schemas.value_line import ValueComponentSummary, ValueLinePoint, ValueLineResponse, ValueLineSummary
from app.services.provider_registry import get_fundamentals_provider


@dataclass(frozen=True)
class ValueLineWeights:
    pe: float = 1.0
    ps: float = 1.0
    pb: float = 1.0
    nav: float = 1.0


class ValueLineService:
    def __init__(self, multiple_lookback: int = 300, weights: ValueLineWeights | None = None):
        self.multiple_lookback = multiple_lookback
        self.weights = weights or ValueLineWeights()

    def build_value_line(self, symbol: str, timeframe: str, frame: pd.DataFrame) -> ValueLineResponse:
        if frame.empty:
            raise ValueError(f"No market data returned for {symbol}")

        time_col = frame.columns[0]
        price_frame = pd.DataFrame(
            {
                "time": pd.to_datetime(frame[time_col]),
                "close": pd.to_numeric(frame["Close"], errors="coerce"),
            }
        ).dropna(subset=["close"]).reset_index(drop=True)

        provider = get_fundamentals_provider()
        snapshot = provider.get_snapshot(symbol)
        time_series = provider.get_time_series(symbol)

        eps = self._align_series(price_frame["time"], time_series.get("eps", pd.Series(dtype=float)), snapshot.get("trailing_eps"))
        revenue = self._align_series(price_frame["time"], time_series.get("revenue", pd.Series(dtype=float)), snapshot.get("total_revenue"))
        shares = self._align_series(price_frame["time"], time_series.get("shares", pd.Series(dtype=float)), snapshot.get("shares_outstanding"))
        equity = self._align_series(price_frame["time"], time_series.get("book_equity", pd.Series(dtype=float)))
        assets = self._align_series(price_frame["time"], time_series.get("total_assets", pd.Series(dtype=float)), snapshot.get("total_assets"))
        liabilities = self._align_series(price_frame["time"], time_series.get("total_liabilities", pd.Series(dtype=float)), snapshot.get("total_liabilities"))

        revenue_per_share = self._safe_divide(revenue, shares)
        book_per_share = self._safe_divide(equity, shares)
        if not pd.isna(snapshot.get("book_value_per_share")):
            book_per_share = book_per_share.fillna(float(snapshot["book_value_per_share"]))
        nav_per_share = self._safe_divide(assets - liabilities, shares)

        fair_pe, current_pe = self._fair_value_from_multiple(price_frame["close"], eps, self.weights.pe)
        fair_ps, current_ps = self._fair_value_from_multiple(price_frame["close"], revenue_per_share, self.weights.ps)
        fair_pb, current_pb = self._fair_value_from_multiple(price_frame["close"], book_per_share, self.weights.pb)
        fair_nav, current_nav = self._fair_value_from_multiple(price_frame["close"], nav_per_share, self.weights.nav)

        weighted_sum = (
            fair_pe.fillna(0.0) * self.weights.pe
            + fair_ps.fillna(0.0) * self.weights.ps
            + fair_pb.fillna(0.0) * self.weights.pb
            + fair_nav.fillna(0.0) * self.weights.nav
        )
        total_weight = (
            fair_pe.notna().astype(float) * self.weights.pe
            + fair_ps.notna().astype(float) * self.weights.ps
            + fair_pb.notna().astype(float) * self.weights.pb
            + fair_nav.notna().astype(float) * self.weights.nav
        )
        fair_value = weighted_sum / total_weight.replace(0.0, np.nan)

        points = [
            ValueLinePoint(time=row.time.to_pydatetime(), fair_value=float(row.fair_value))
            for row in pd.DataFrame({"time": price_frame["time"], "fair_value": fair_value}).dropna().itertuples(index=False)
        ]

        current_price = float(price_frame["close"].iloc[-1])
        current_fair_value = float(fair_value.iloc[-1]) if pd.notna(fair_value.iloc[-1]) else None
        upside_pct = ((current_fair_value / current_price) - 1) * 100 if current_fair_value is not None and current_price else None
        price_vs_value_pct = ((current_price / current_fair_value) - 1) * 100 if current_fair_value not in (None, 0) else None
        active_models = sum(value is not None for value in [current_pe, current_ps, current_pb, current_nav])

        components = [
            ValueComponentSummary(name="P/E", fair_value=current_pe),
            ValueComponentSummary(name="P/S", fair_value=current_ps),
            ValueComponentSummary(name="P/B", fair_value=current_pb),
            ValueComponentSummary(name="P/NAV", fair_value=current_nav),
        ]

        return ValueLineResponse(
            symbol=symbol,
            timeframe=timeframe,
            anchor_time=price_frame["time"].iloc[-1].to_pydatetime(),
            current_price=current_price,
            lookback_bars=min(self.multiple_lookback, len(price_frame)),
            points=points,
            summary=ValueLineSummary(
                fair_value=current_fair_value,
                upside_pct=round(upside_pct, 2) if upside_pct is not None else None,
                price_vs_value_pct=round(price_vs_value_pct, 2) if price_vs_value_pct is not None else None,
                active_models=active_models,
                signal=self._signal_label(upside_pct, active_models),
            ),
            components=components,
        )

    def _fair_value_from_multiple(self, close: pd.Series, metric_per_share: pd.Series, weight: float) -> tuple[pd.Series, float | None]:
        if weight <= 0:
            return pd.Series(np.nan, index=close.index, dtype=float), None

        valid_metric = metric_per_share.where(metric_per_share > 0)
        multiple = close / valid_metric
        average_multiple = multiple.rolling(
            self.multiple_lookback,
            min_periods=min(60, max(20, self.multiple_lookback // 3)),
        ).mean()
        fair_value = valid_metric * average_multiple
        current_value = float(fair_value.iloc[-1]) if len(fair_value) and pd.notna(fair_value.iloc[-1]) else None
        return fair_value, current_value

    def _align_series(self, price_times: pd.Series, series: pd.Series, fallback: float | None = None) -> pd.Series:
        aligned = pd.Series(np.nan, index=price_times.index, dtype=float)
        if series is not None and not series.empty:
            values = pd.DataFrame(
                {
                    "effective_time": pd.to_datetime(series.index),
                    "value": pd.to_numeric(series, errors="coerce"),
                }
            ).dropna().sort_values("effective_time")
            if not values.empty:
                aligned = pd.merge_asof(
                    pd.DataFrame({"time": pd.to_datetime(price_times)}),
                    values,
                    left_on="time",
                    right_on="effective_time",
                    direction="backward",
                )["value"]
        if fallback is not None and not pd.isna(fallback):
            aligned = aligned.fillna(float(fallback))
        return pd.to_numeric(aligned, errors="coerce")

    def _safe_divide(self, numerator: pd.Series, denominator: pd.Series) -> pd.Series:
        result = numerator / denominator.replace(0.0, np.nan)
        return pd.to_numeric(result, errors="coerce")

    def _signal_label(self, upside_pct: float | None, active_models: int) -> str:
        if active_models == 0 or upside_pct is None:
            return "unavailable"
        if upside_pct >= 30:
            return "deeply undervalued"
        if upside_pct >= 12:
            return "undervalued"
        if upside_pct <= -20:
            return "overvalued"
        if upside_pct <= -8:
            return "rich"
        return "near value"
