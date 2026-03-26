from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from app.schemas.macro import MacroFactorExposure, MacroImpactSummary
from app.services.provider_registry import get_macro_provider


@dataclass(frozen=True)
class MacroFactorSpec:
    key: str
    label: str
    positive_state: str
    negative_state: str


class MacroImpactService:
    FACTOR_SPECS = (
        MacroFactorSpec("rates", "Rates", "yields rising", "yields easing"),
        MacroFactorSpec("curve", "Curve", "curve steepening", "curve flattening"),
        MacroFactorSpec("inflation", "Inflation", "inflation firming", "inflation cooling"),
        MacroFactorSpec("labor", "Labor", "labor weakening", "labor improving"),
        MacroFactorSpec("credit", "Credit", "credit stress rising", "credit easing"),
    )

    def build_summary(self, frame: pd.DataFrame) -> MacroImpactSummary:
        if frame.empty:
            return self._unavailable_summary()

        try:
            price_frame = self._build_price_frame(frame)
            factor_frame = self._build_factor_frame(price_frame["time"])
            aligned = pd.concat([price_frame.set_index("time"), factor_frame], axis=1).dropna()
            if len(aligned) < 80:
                return self._unavailable_summary()

            stock_returns = np.log(aligned["close"] / aligned["close"].shift(1)).dropna()
            factor_values = aligned[self.factor_keys].reindex(stock_returns.index).dropna()
            stock_returns = stock_returns.reindex(factor_values.index).dropna()
            if len(stock_returns) < 60 or factor_values.empty:
                return self._unavailable_summary()

            common = pd.concat([stock_returns.rename("stock"), factor_values], axis=1).dropna().tail(252)
            if len(common) < 60:
                return self._unavailable_summary()

            y = self._standardize(common["stock"])
            x = common[self.factor_keys].apply(self._standardize)
            if y.isna().all() or x.isna().all(axis=None):
                return self._unavailable_summary()

            design = np.column_stack([np.ones(len(x)), x.to_numpy()])
            coefficients, *_ = np.linalg.lstsq(design, y.to_numpy(), rcond=None)
            sensitivities = coefficients[1:]
            current_row = factor_frame.dropna().iloc[-1]

            exposures: list[MacroFactorExposure] = []
            for spec, sensitivity in zip(self.FACTOR_SPECS, sensitivities, strict=False):
                current_z = float(current_row.get(spec.key, 0.0))
                impact_score = float(sensitivity * current_z)
                direction = "tailwind" if impact_score > 0.08 else "headwind" if impact_score < -0.08 else "neutral"
                exposures.append(
                    MacroFactorExposure(
                        factor=spec.key,
                        label=self._state_label(spec, current_z),
                        current_z=round(current_z, 2),
                        sensitivity=round(float(sensitivity), 2),
                        impact_score=round(impact_score, 2),
                        direction=direction,
                    )
                )

            total_score = float(sum(exposure.impact_score for exposure in exposures))
            signal = "supportive" if total_score > 0.35 else "headwind" if total_score < -0.35 else "neutral"
            sorted_exposures = sorted(exposures, key=lambda exposure: abs(exposure.impact_score), reverse=True)
            tailwind_factor = next((exposure.label for exposure in sorted_exposures if exposure.impact_score > 0.08), None)
            headwind_factor = next((exposure.label for exposure in sorted_exposures if exposure.impact_score < -0.08), None)
            regime_label = self._regime_label(signal, sorted_exposures)

            return MacroImpactSummary(
                regime_label=regime_label,
                signal=signal,
                score=round(total_score, 2),
                tailwind_factor=tailwind_factor,
                headwind_factor=headwind_factor,
                exposures=sorted_exposures,
            )
        except Exception:
            return self._unavailable_summary()

    @property
    def factor_keys(self) -> list[str]:
        return [spec.key for spec in self.FACTOR_SPECS]

    def _build_price_frame(self, frame: pd.DataFrame) -> pd.DataFrame:
        normalized = frame.copy()
        if isinstance(normalized.columns, pd.MultiIndex):
            normalized.columns = [column[0] for column in normalized.columns]

        time_col = normalized.columns[0]
        return pd.DataFrame(
            {
                "time": pd.to_datetime(normalized[time_col]),
                "close": pd.to_numeric(normalized["Close"], errors="coerce"),
            }
        ).dropna().set_index("time").sort_index().reset_index()

    def _build_factor_frame(self, price_times: pd.Series) -> pd.DataFrame:
        provider = get_macro_provider()
        start = (pd.to_datetime(price_times.iloc[0]) - pd.DateOffset(years=5)).strftime("%Y-%m-%d")
        end = pd.to_datetime(price_times.iloc[-1]).strftime("%Y-%m-%d")

        ten_year = self._aligned_series(provider, price_times, "DGS10", start, end)
        two_year = self._aligned_series(provider, price_times, "DGS2", start, end)
        cpi = self._aligned_series(provider, price_times, "CPIAUCSL", start, end)
        unemployment = self._aligned_series(provider, price_times, "UNRATE", start, end)
        credit_spread = self._aligned_series(provider, price_times, "BAA10Y", start, end)

        curve = ten_year - two_year
        inflation_yoy = cpi.pct_change(252) * 100

        factor_frame = pd.DataFrame(index=pd.to_datetime(price_times))
        factor_frame["rates"] = self._rolling_zscore(ten_year.diff(21))
        factor_frame["curve"] = self._rolling_zscore(curve.diff(21))
        factor_frame["inflation"] = self._rolling_zscore(inflation_yoy.diff(63))
        factor_frame["labor"] = self._rolling_zscore(unemployment.diff(63))
        factor_frame["credit"] = self._rolling_zscore(credit_spread.diff(21))
        return factor_frame.replace([np.inf, -np.inf], np.nan)

    def _aligned_series(
        self,
        provider,
        price_times: pd.Series,
        series_name: str,
        start: str,
        end: str,
    ) -> pd.Series:
        data = provider.get_series(series_name, start, end).copy()
        if data.empty:
            return pd.Series(np.nan, index=pd.to_datetime(price_times), dtype=float)

        data["date"] = pd.to_datetime(data["date"])
        data["value"] = pd.to_numeric(data["value"], errors="coerce")
        data = data.dropna().sort_values("date")
        if data.empty:
            return pd.Series(np.nan, index=pd.to_datetime(price_times), dtype=float)

        aligned = pd.merge_asof(
            pd.DataFrame({"time": pd.to_datetime(price_times).sort_values()}),
            data,
            left_on="time",
            right_on="date",
            direction="backward",
        )["value"]
        return pd.Series(pd.to_numeric(aligned, errors="coerce").to_numpy(), index=pd.to_datetime(price_times), dtype=float)

    def _rolling_zscore(self, series: pd.Series, window: int = 252) -> pd.Series:
        mean = series.rolling(window, min_periods=80).mean()
        std = series.rolling(window, min_periods=80).std().replace(0.0, np.nan)
        return (series - mean) / std

    def _standardize(self, series: pd.Series) -> pd.Series:
        std = series.std()
        if pd.isna(std) or std == 0:
            return pd.Series(np.nan, index=series.index, dtype=float)
        return (series - series.mean()) / std

    def _state_label(self, spec: MacroFactorSpec, current_z: float) -> str:
        if current_z >= 0.35:
            return spec.positive_state
        if current_z <= -0.35:
            return spec.negative_state
        return f"{spec.label.lower()} stable"

    def _regime_label(self, signal: str, exposures: list[MacroFactorExposure]) -> str:
        if not exposures:
            return "macro unavailable"
        top = exposures[0].label
        return f"{signal} / {top}"

    def _unavailable_summary(self) -> MacroImpactSummary:
        return MacroImpactSummary(
            regime_label="macro unavailable",
            signal="unavailable",
            score=0.0,
            tailwind_factor=None,
            headwind_factor=None,
            exposures=[],
        )
