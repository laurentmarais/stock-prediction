import { useEffect, useState } from "react";

import { ChartPanel } from "./components/ChartPanel";
import { RegimeStrip } from "./components/RegimeStrip";
import { ReplayTable } from "./components/ReplayTable";
import { ScenarioPanel } from "./components/ScenarioPanel";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
const TIMEFRAMES = ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1wk", "1mo"];

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

type ValueLineSummary = {
  fair_value: number | null;
  upside_pct: number | null;
  price_vs_value_pct: number | null;
  active_models: number;
  signal: string;
};

type MacroFactorExposure = {
  factor: string;
  label: string;
  current_z: number;
  sensitivity: number;
  impact_score: number;
  direction: string;
};

type MacroImpactSummary = {
  regime_label: string;
  signal: string;
  score: number;
  tailwind_factor: string | null;
  headwind_factor: string | null;
  exposures: MacroFactorExposure[];
};

type ValueLineResponse = {
  symbol: string;
  timeframe: string;
  anchor_time: string;
  current_price: number;
  lookback_bars: number;
  points: ValueLinePoint[];
  summary: ValueLineSummary;
  components: { name: string; fair_value: number | null }[];
};

type ReplaySummary = {
  realizedReturnPct: number | null;
  maxDrawdownPct: number | null;
  endedInsideOuterBand: boolean | null;
  endedInsideInnerBand: boolean | null;
  medianErrorPct: number | null;
};

type ForecastResponse = {
  anchor_time: string;
  regime_label: string;
  regime_match_count: number;
  probability_up: number;
  probability_up_5: number;
  probability_up_10: number;
  probability_down_5: number;
  probability_down_10: number;
  forecast: ForecastPoint[];
  regime_history: { time: string; regime: string }[];
  scenarios: { name: string; probability: number; description: string }[];
  macro: MacroImpactSummary;
  value_line: ValueLineSummary;
};

type SymbolProfile = {
  symbol: string;
  requested_symbol: string;
  company_name: string | null;
  display_name: string | null;
  exchange: string | null;
  exchange_code: string | null;
  quote_type: string | null;
  sector: string | null;
  industry: string | null;
  matched_exact_symbol: boolean;
};

async function fetchJson<T>(url: string): Promise<T> {
  const response = await fetch(url);
  const contentType = response.headers.get("content-type") ?? "";
  const payload = contentType.includes("application/json") ? await response.json() : await response.text();

  if (!response.ok) {
    const detail = typeof payload === "object" && payload && "detail" in payload
      ? String(payload.detail)
      : response.statusText || "Request failed";
    throw new Error(detail);
  }

  return payload as T;
}

export default function App() {
  const [symbolInput, setSymbolInput] = useState("AAPL");
  const [symbol, setSymbol] = useState("AAPL");
  const [timeframe, setTimeframe] = useState("1d");
  const [replayDate, setReplayDate] = useState("");
  const [bars, setBars] = useState<Bar[]>([]);
  const [fullHistory, setFullHistory] = useState<Bar[]>([]);
  const [realizedPath, setRealizedPath] = useState<RealizedPoint[]>([]);
  const [valueLine, setValueLine] = useState<ValueLineResponse | null>(null);
  const [forecast, setForecast] = useState<ForecastResponse | null>(null);
  const [symbolProfile, setSymbolProfile] = useState<SymbolProfile | null>(null);
  const [providers, setProviders] = useState<Record<string, { selected: string; available: string[] }> | null>(null);
  const [dataError, setDataError] = useState<string | null>(null);

  const normalizedSymbolInput = symbolInput.trim().toUpperCase();
  const companyName = symbolProfile?.company_name ?? symbolProfile?.display_name;
  const companyMeta = [symbolProfile?.exchange, symbolProfile?.quote_type].filter(Boolean).join(" • ");

  const replayIndex = replayDate
    ? fullHistory.findIndex((bar) => bar.time.startsWith(replayDate.slice(0, 10)))
    : -1;

  const replaySummary: ReplaySummary = (() => {
    if (!forecast || bars.length === 0 || realizedPath.length === 0) {
      return {
        realizedReturnPct: null,
        maxDrawdownPct: null,
        endedInsideOuterBand: null,
        endedInsideInnerBand: null,
        medianErrorPct: null,
      };
    }

    const anchorPrice = bars[bars.length - 1]?.close;
    const endRealized = realizedPath[realizedPath.length - 1]?.value;
    const lastForecast = forecast.forecast[Math.min(realizedPath.length, forecast.forecast.length) - 1];
    if (!anchorPrice || !endRealized || !lastForecast) {
      return {
        realizedReturnPct: null,
        maxDrawdownPct: null,
        endedInsideOuterBand: null,
        endedInsideInnerBand: null,
        medianErrorPct: null,
      };
    }

    const realizedReturnPct = ((endRealized / anchorPrice) - 1) * 100;
    const minRealized = Math.min(...realizedPath.map((point) => point.value));
    const maxDrawdownPct = ((minRealized / anchorPrice) - 1) * 100;
    const endedInsideOuterBand = endRealized >= lastForecast.p10 && endRealized <= lastForecast.p90;
    const endedInsideInnerBand = endRealized >= lastForecast.p25 && endRealized <= lastForecast.p75;
    const medianErrorPct = ((endRealized / lastForecast.p50) - 1) * 100;

    return {
      realizedReturnPct,
      maxDrawdownPct,
      endedInsideOuterBand,
      endedInsideInnerBand,
      medianErrorPct,
    };
  })();

  useEffect(() => {
    let cancelled = false;

    void fetchJson<Record<string, { selected: string; available: string[] }>>(`${API_BASE_URL}/api/providers`)
      .then((providerData) => {
        if (!cancelled) {
          setProviders(providerData);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setProviders(null);
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;

    void fetchJson<SymbolProfile>(`${API_BASE_URL}/api/symbols/profile?symbol=${encodeURIComponent(symbol)}`)
      .then((profile) => {
        if (!cancelled) {
          setSymbolProfile(profile);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setSymbolProfile(null);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [symbol]);

  useEffect(() => {
    let cancelled = false;

    setDataError(null);
    setFullHistory([]);
    setBars([]);
    setValueLine(null);
    setForecast(null);
    setRealizedPath([]);

    void fetchJson<Bar[]>(`${API_BASE_URL}/api/chart?symbol=${encodeURIComponent(symbol)}&timeframe=${encodeURIComponent(timeframe)}`)
      .then((historyData) => {
        if (!cancelled) {
          setFullHistory(historyData);
        }
      })
      .catch((error: Error) => {
        if (!cancelled) {
          setDataError(`Unable to load ${symbol}: ${error.message}`);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [symbol, timeframe]);

  useEffect(() => {
    if (fullHistory.length === 0) {
      return;
    }

    const params = new URLSearchParams({ symbol, timeframe });
    if (replayDate) {
      params.set("as_of", replayDate);
    }

    let cancelled = false;

    void Promise.all([
      fetchJson<Bar[]>(`${API_BASE_URL}/api/chart?${params.toString()}`),
      fetchJson<ForecastResponse>(`${API_BASE_URL}/api/forecast?${params.toString()}&horizon_bars=20`),
      fetchJson<ValueLineResponse>(`${API_BASE_URL}/api/value-line?${params.toString()}`),
    ])
      .then(([chartData, forecastData, valueLineData]) => {
        if (cancelled) {
          return;
        }

        setBars(chartData);
        setForecast(forecastData);
        setValueLine(valueLineData);
        setDataError(null);

        if (replayDate) {
          const anchor = new Date(replayDate).getTime();
          const futurePath = fullHistory
            .filter((bar) => new Date(bar.time).getTime() > anchor)
            .slice(0, 20)
            .map((bar) => ({ time: bar.time, value: bar.close }));
          setRealizedPath(futurePath);
        } else {
          setRealizedPath([]);
        }
      })
      .catch((error: Error) => {
        if (!cancelled) {
          setBars([]);
          setValueLine(null);
          setForecast(null);
          setRealizedPath([]);
          setDataError(`Unable to load ${symbol}: ${error.message}`);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [symbol, timeframe, replayDate, fullHistory]);

  const sliderMax = Math.max(fullHistory.length - 2, 0);

  function commitSymbol(): void {
    if (!normalizedSymbolInput) {
      setSymbolInput(symbol);
      return;
    }

    setReplayDate("");
    setSymbol(normalizedSymbolInput);
    setSymbolInput(normalizedSymbolInput);
  }

  function handleReplayScrub(index: number): void {
    const bar = fullHistory[index];
    if (!bar) {
      return;
    }
    setReplayDate(bar.time.slice(0, 16));
  }

  return (
    <main className="app-shell">
      <header className="top-bar">
        <div className="brand">Stock Future Probability Engine</div>
        <form
          className="symbol-form"
          onSubmit={(event) => {
            event.preventDefault();
            commitSymbol();
          }}
        >
          <input
            aria-label="Symbol"
            placeholder="Ticker"
            value={symbolInput}
            onChange={(event) => setSymbolInput(event.target.value.toUpperCase())}
          />
          <button className="ghost-button" type="submit">Load</button>
        </form>
        <input aria-label="Replay date" type="datetime-local" value={replayDate} onChange={(event) => setReplayDate(event.target.value)} />
        <button className="ghost-button" onClick={() => setReplayDate("")} type="button">Latest</button>
        <div className="timeframes">
          {TIMEFRAMES.map((value) => (
            <button
              className={value === timeframe ? "active" : ""}
              key={value}
              onClick={() => setTimeframe(value)}
              type="button"
            >
              {value}
            </button>
          ))}
        </div>
      </header>

      <section className="workspace">
        <div className="main-panel">
          <div className="panel-header">
            <h1>{symbol}</h1>
            <p>
              {companyName ? `${companyName}${companyMeta ? ` • ${companyMeta}` : ""}` : "Historical candles plus forecast bands generated from free sources and replay-aware history cuts."}
            </p>
            {symbolProfile?.sector && symbolProfile?.industry ? (
              <p>{`${symbolProfile.sector} • ${symbolProfile.industry}`}</p>
            ) : null}
          </div>
          {dataError ? <div className="status-banner error-banner">{dataError}</div> : null}
          <div className="replay-toolbar">
            <div className="replay-toolbar-copy">
              <span className="eyebrow">Replay Scrubber</span>
              <strong>{replayDate ? new Date(replayDate).toLocaleString() : "Latest available bar"}</strong>
            </div>
            <input
              aria-label="Replay scrubber"
              className="replay-slider"
              max={sliderMax}
              min={0}
              onChange={(event) => handleReplayScrub(Number(event.target.value))}
              type="range"
              value={replayIndex >= 0 ? replayIndex : sliderMax}
            />
          </div>
          <div className="anchor-banner">
            <span className="anchor-badge">Anchor</span>
            <span>{forecast?.anchor_time ? new Date(forecast.anchor_time).toLocaleString() : "Latest"}</span>
          </div>
          <ChartPanel
            bars={bars}
            forecast={forecast?.forecast ?? []}
            realizedPath={realizedPath}
            valueLine={valueLine?.points ?? []}
            macroSummary={forecast?.macro ?? null}
          />
          <RegimeStrip currentRegime={forecast?.regime_label ?? "n/a"} history={forecast?.regime_history ?? []} />
          <ReplayTable anchorPrice={bars[bars.length - 1]?.close ?? null} forecast={forecast?.forecast ?? []} realizedPath={realizedPath} />
        </div>

        <ScenarioPanel
          probabilityUp={forecast?.probability_up ?? 0}
          probabilityUp5={forecast?.probability_up_5 ?? 0}
          probabilityUp10={forecast?.probability_up_10 ?? 0}
          probabilityDown5={forecast?.probability_down_5 ?? 0}
          probabilityDown10={forecast?.probability_down_10 ?? 0}
          anchorTime={forecast?.anchor_time ?? ""}
          regimeLabel={forecast?.regime_label ?? "n/a"}
          regimeMatchCount={forecast?.regime_match_count ?? 0}
          scenarios={forecast?.scenarios ?? []}
          providers={providers}
          replaySummary={replaySummary}
          macroSummary={forecast?.macro ?? null}
          valueLineSummary={forecast?.value_line ?? valueLine?.summary ?? null}
        />
      </section>
    </main>
  );
}
