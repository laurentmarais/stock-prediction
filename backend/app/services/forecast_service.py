from __future__ import annotations

from datetime import timedelta

import numpy as np
import pandas as pd

from app.schemas.forecast import ForecastBandPoint, ForecastResponse, RegimePoint, ScenarioCard


class ForecastService:
    def build_forecast(self, symbol: str, timeframe: str, frame: pd.DataFrame, horizon_bars: int) -> ForecastResponse:
        if frame.empty:
            raise ValueError(f"No market data returned for {symbol}")

        closes = frame["Close"].astype(float)
        returns = np.log(closes / closes.shift(1)).dropna()
        if returns.empty:
            raise ValueError(f"Not enough history returned for {symbol}")

        anchor_time = pd.to_datetime(frame.iloc[-1][frame.columns[0]])
        current_price = float(closes.to_numpy()[-1])
        time_values = pd.to_datetime(frame.iloc[1:][frame.columns[0]]).reset_index(drop=True)
        regime_frame = self._build_regime_frame(closes, returns, time_values)
        regime_label, regime_match_count, simulated_paths = self._simulate_paths(current_price, returns, regime_frame, horizon_bars)
        quantiles = np.quantile(simulated_paths, [0.10, 0.25, 0.50, 0.75, 0.90], axis=0)

        bands: list[ForecastBandPoint] = []
        for index in range(horizon_bars):
            point_time = anchor_time + self._time_delta_for(timeframe, index + 1)
            bands.append(
                ForecastBandPoint(
                    time=point_time.to_pydatetime(),
                    p10=float(quantiles[0][index]),
                    p25=float(quantiles[1][index]),
                    p50=float(quantiles[2][index]),
                    p75=float(quantiles[3][index]),
                    p90=float(quantiles[4][index]),
                )
            )

        end_values = simulated_paths[:, -1]
        probability_up = float(np.mean(end_values > current_price))
        probability_up_5 = float(np.mean(end_values >= current_price * 1.05))
        probability_up_10 = float(np.mean(end_values >= current_price * 1.10))
        probability_down_5 = float(np.mean(np.min(simulated_paths, axis=1) <= current_price * 0.95))
        probability_down_10 = float(np.mean(np.min(simulated_paths, axis=1) <= current_price * 0.90))

        scenarios = [
            ScenarioCard(
                name="Bull",
                probability=round(probability_up_10, 3),
                description="Upper-tail continuation using realized return and volatility history available at the anchor time.",
            ),
            ScenarioCard(
                name="Base",
                probability=round(max(probability_up - probability_up_10, 0.0), 3),
                description="Range-bound to mildly positive outcome around the median path.",
            ),
            ScenarioCard(
                name="Bear",
                probability=round(max(probability_down_5 - probability_down_10, 0.0), 3),
                description="Moderate downside path with weaker drift and higher realized drawdown.",
            ),
            ScenarioCard(
                name="Tail",
                probability=round(probability_down_10, 3),
                description="Large downside path implied by the lower tail of simulated outcomes.",
            ),
        ]

        regime_history = [
            RegimePoint(time=row["time"].to_pydatetime(), regime=row["regime"])
            for _, row in regime_frame.tail(40).iterrows()
        ]

        return ForecastResponse(
            symbol=symbol,
            timeframe=timeframe,
            horizon_bars=horizon_bars,
            anchor_time=anchor_time.to_pydatetime(),
            regime_label=regime_label,
            regime_match_count=regime_match_count,
            current_price=current_price,
            probability_up=round(probability_up, 3),
            probability_down_5=round(probability_down_5, 3),
            probability_up_5=round(probability_up_5, 3),
            probability_down_10=round(probability_down_10, 3),
            probability_up_10=round(probability_up_10, 3),
            scenarios=scenarios,
            forecast=bands,
            regime_history=regime_history,
        )

    def _simulate_paths(
        self,
        current_price: float,
        returns: pd.Series,
        regime_frame: pd.DataFrame,
        horizon_bars: int,
        paths: int = 2000,
    ) -> tuple[str, int, np.ndarray]:
        current_regime = regime_frame["regime"].iloc[-1]
        candidate_positions = regime_frame.loc[regime_frame["regime"] == current_regime, "position"].tolist()
        candidate_positions = [index for index in candidate_positions if index + horizon_bars < len(returns)]

        if len(candidate_positions) >= 25:
            sampled = np.vstack(
                [
                    returns.iloc[start + 1 : start + 1 + horizon_bars].to_numpy()
                    for start in np.random.choice(candidate_positions, size=paths, replace=True)
                ]
            )
        else:
            sampled = np.random.choice(returns.to_numpy(), size=(paths, horizon_bars), replace=True)

        cumulative = np.cumsum(sampled, axis=1)
        simulated_paths = current_price * np.exp(cumulative)
        return current_regime, len(candidate_positions), simulated_paths

    def _build_regime_frame(self, closes: pd.Series, returns: pd.Series, time_values: pd.Series) -> pd.DataFrame:
        vol_20 = returns.rolling(20).std() * np.sqrt(252)
        trend_60 = closes.pct_change(60).reindex(returns.index)

        valid_vol = vol_20.dropna()
        if valid_vol.empty:
            return pd.DataFrame(
                {
                    "position": np.arange(len(returns)),
                    "time": time_values,
                    "regime": ["normal-vol / flat-trend"] * len(returns),
                }
            )

        low_cut = valid_vol.quantile(0.33)
        high_cut = valid_vol.quantile(0.67)

        def label_row(index: pd.Timestamp) -> str:
            vol_value = vol_20.loc[index]
            trend_value = trend_60.loc[index] if index in trend_60.index else np.nan

            if pd.isna(vol_value):
                vol_label = "normal-vol"
            elif vol_value <= low_cut:
                vol_label = "low-vol"
            elif vol_value >= high_cut:
                vol_label = "high-vol"
            else:
                vol_label = "normal-vol"

            if pd.isna(trend_value):
                trend_label = "flat-trend"
            elif trend_value > 0.05:
                trend_label = "up-trend"
            elif trend_value < -0.05:
                trend_label = "down-trend"
            else:
                trend_label = "flat-trend"

            return f"{vol_label} / {trend_label}"

        return pd.DataFrame(
            {
                "position": np.arange(len(returns)),
                "time": time_values,
                "regime": [label_row(index) for index in returns.index],
            }
        )

    def _time_delta_for(self, timeframe: str, bars_ahead: int) -> timedelta:
        mapping = {
            "1m": timedelta(minutes=bars_ahead),
            "5m": timedelta(minutes=5 * bars_ahead),
            "15m": timedelta(minutes=15 * bars_ahead),
            "30m": timedelta(minutes=30 * bars_ahead),
            "1h": timedelta(hours=bars_ahead),
            "4h": timedelta(hours=4 * bars_ahead),
            "1d": timedelta(days=bars_ahead),
            "1wk": timedelta(weeks=bars_ahead),
            "1mo": timedelta(days=30 * bars_ahead),
        }
        return mapping.get(timeframe, timedelta(days=bars_ahead))