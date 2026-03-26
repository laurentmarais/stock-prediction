import { useEffect, useRef } from "react";
import { BaselineSeries, CandlestickSeries, ColorType, LineSeries, createChart } from "lightweight-charts";

type Bar = {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
};

type ForecastPoint = {
  time: string;
  p10: number;
  p25: number;
  p50: number;
  p75: number;
  p90: number;
};

type RealizedPoint = {
  time: string;
  value: number;
};

type ValueLinePoint = {
  time: string;
  fair_value: number;
};

type MacroImpactSummary = {
  regime_label: string;
  signal: string;
  score: number;
  tailwind_factor: string | null;
  headwind_factor: string | null;
};

type Props = {
  bars: Bar[];
  forecast: ForecastPoint[];
  realizedPath: RealizedPoint[];
  valueLine: ValueLinePoint[];
  macroSummary: MacroImpactSummary | null;
};

export function ChartPanel({ bars, forecast, realizedPath, valueLine, macroSummary }: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!containerRef.current) {
      return;
    }

    const chart = createChart(containerRef.current, {
      autoSize: true,
      layout: {
        background: { type: ColorType.Solid, color: "#07111f" },
        textColor: "#d9e2ec",
      },
      grid: {
        vertLines: { color: "rgba(255,255,255,0.04)" },
        horzLines: { color: "rgba(255,255,255,0.04)" },
      },
      rightPriceScale: {
        borderColor: "rgba(255,255,255,0.08)",
      },
      timeScale: {
        borderColor: "rgba(255,255,255,0.08)",
      },
    });

    const candles = chart.addSeries(CandlestickSeries, {
      upColor: "#5ac27a",
      downColor: "#ef6351",
      borderDownColor: "#ef6351",
      borderUpColor: "#5ac27a",
      wickDownColor: "#ef6351",
      wickUpColor: "#5ac27a",
    });

    candles.setData(
      bars.map((bar) => ({
        time: Math.floor(new Date(bar.time).getTime() / 1000) as never,
        open: bar.open,
        high: bar.high,
        low: bar.low,
        close: bar.close,
      }))
    );

    const valueLineSeries = chart.addSeries(LineSeries, {
      color: "#2ec4b6",
      lineWidth: 2,
    });
    valueLineSeries.setData(
      valueLine.map((point) => ({
        time: Math.floor(new Date(point.time).getTime() / 1000) as never,
        value: point.fair_value,
      }))
    );

    const upperBound = chart.addSeries(LineSeries, {
      color: "rgba(90, 169, 255, 0.95)",
      lineWidth: 2,
      lineStyle: 3,
    });
    upperBound.setData(
      forecast.map((point) => ({
        time: Math.floor(new Date(point.time).getTime() / 1000) as never,
        value: point.p90,
      }))
    );

    const lowerBound = chart.addSeries(LineSeries, {
      color: "rgba(90, 169, 255, 0.95)",
      lineWidth: 2,
      lineStyle: 3,
    });
    lowerBound.setData(
      forecast.map((point) => ({
        time: Math.floor(new Date(point.time).getTime() / 1000) as never,
        value: point.p10,
      }))
    );

    const median = chart.addSeries(BaselineSeries, {
      topLineColor: "#ffd166",
      topFillColor1: "rgba(255, 209, 102, 0.18)",
      topFillColor2: "rgba(255, 209, 102, 0.04)",
      bottomLineColor: "#ffd166",
      bottomFillColor1: "rgba(255, 209, 102, 0.04)",
      bottomFillColor2: "rgba(255, 209, 102, 0.01)",
      lineWidth: 2,
      baseValue: { type: "price", price: bars.length ? bars[bars.length - 1].close : 0 },
    });
    median.setData(
      forecast.map((point) => ({
        time: Math.floor(new Date(point.time).getTime() / 1000) as never,
        value: point.p50,
      }))
    );

    const realized = chart.addSeries(LineSeries, {
      color: "#f28482",
      lineWidth: 2,
      lineStyle: 2,
    });
    realized.setData(
      realizedPath.map((point) => ({
        time: Math.floor(new Date(point.time).getTime() / 1000) as never,
        value: point.value,
      }))
    );

    chart.timeScale().fitContent();
    return () => chart.remove();
  }, [bars, forecast, realizedPath, valueLine]);

  return (
    <div className="chart-panel-wrap">
      <div className="chart-legend">
        <span className="chart-legend-item">
          <span className="chart-legend-swatch chart-legend-swatch-candles" />
          Price candles
        </span>
        <span className="chart-legend-item">
          <span className="chart-legend-swatch chart-legend-swatch-value-line" />
          Value line
        </span>
        <span className="chart-legend-item">
          <span className="chart-legend-swatch chart-legend-swatch-range" />
          Forecast range 10-90%
        </span>
        <span className="chart-legend-item">
          <span className="chart-legend-swatch chart-legend-swatch-median" />
          Median forecast
        </span>
        <span className="chart-legend-item">
          <span className="chart-legend-swatch chart-legend-swatch-realized" />
          Realized path
        </span>
      </div>
      <div className="chart-macro-strip">
        <span className={`chart-macro-badge chart-macro-${macroSummary?.signal ?? "unavailable"}`}>{macroSummary?.signal ?? "unavailable"}</span>
        <span className="chart-macro-copy">{macroSummary?.regime_label ?? "Macro regime unavailable"}</span>
        {macroSummary?.tailwind_factor ? <span className="chart-macro-detail">Tailwind: {macroSummary.tailwind_factor}</span> : null}
        {macroSummary?.headwind_factor ? <span className="chart-macro-detail">Headwind: {macroSummary.headwind_factor}</span> : null}
      </div>
      <div className="chart-panel" ref={containerRef} />
    </div>
  );
}
