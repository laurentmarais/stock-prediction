type Scenario = {
  name: string;
  probability: number;
  description: string;
};

type Props = {
  probabilityUp: number;
  probabilityUp5: number;
  probabilityUp10: number;
  probabilityDown5: number;
  probabilityDown10: number;
  anchorTime: string;
  regimeLabel: string;
  regimeMatchCount: number;
  scenarios: Scenario[];
  providers: Record<string, { selected: string; available: string[] }> | null;
  replaySummary: {
    realizedReturnPct: number | null;
    maxDrawdownPct: number | null;
    endedInsideOuterBand: boolean | null;
    endedInsideInnerBand: boolean | null;
    medianErrorPct: number | null;
  };
  macroSummary: {
    regime_label: string;
    signal: string;
    score: number;
    tailwind_factor: string | null;
    headwind_factor: string | null;
    exposures: {
      factor: string;
      label: string;
      current_z: number;
      sensitivity: number;
      impact_score: number;
      direction: string;
    }[];
  } | null;
  valueLineSummary: {
    fair_value: number | null;
    upside_pct: number | null;
    price_vs_value_pct: number | null;
    active_models: number;
    signal: string;
  } | null;
};

function formatPct(value: number | null): string {
  if (value === null) {
    return "n/a";
  }
  const rounded = value.toFixed(1);
  return `${value > 0 ? "+" : ""}${rounded}%`;
}

export function ScenarioPanel(props: Props) {
  return (
    <aside className="scenario-panel">
      <section>
        <h2>Replay Anchor</h2>
        <div className="scenario-card">
          <span className="eyebrow">Forecast Built From</span>
          <strong>{props.anchorTime ? new Date(props.anchorTime).toLocaleString() : "Latest"}</strong>
        </div>
      </section>

      <section>
        <h2>Regime</h2>
        <div className="scenario-card">
          <span className="eyebrow">Current Market State</span>
          <strong>{props.regimeLabel}</strong>
          <p>{props.regimeMatchCount} historical regime matches were available for the current horizon sampler.</p>
        </div>
      </section>

      <section>
        <h2>Macro</h2>
        <div className="scenario-card">
          <span className="eyebrow">Current Environment</span>
          <strong>{props.macroSummary?.regime_label ?? "macro unavailable"}</strong>
          <p>
            Signal: {props.macroSummary?.signal ?? "unavailable"}
            {props.macroSummary ? ` • Score ${props.macroSummary.score > 0 ? "+" : ""}${props.macroSummary.score.toFixed(2)}` : ""}
          </p>
          <p>
            Tailwind: {props.macroSummary?.tailwind_factor ?? "n/a"}
            {" • "}
            Headwind: {props.macroSummary?.headwind_factor ?? "n/a"}
          </p>
        </div>
        <div className="scenario-list macro-factor-list">
          {(props.macroSummary?.exposures ?? []).slice(0, 5).map((exposure) => (
            <article className="scenario-card" key={exposure.factor}>
              <div className="scenario-head">
                <span>{exposure.label}</span>
                <strong>{exposure.direction}</strong>
              </div>
              <p>{`Sensitivity ${exposure.sensitivity > 0 ? "+" : ""}${exposure.sensitivity.toFixed(2)} • Current z ${exposure.current_z > 0 ? "+" : ""}${exposure.current_z.toFixed(2)} • Impact ${exposure.impact_score > 0 ? "+" : ""}${exposure.impact_score.toFixed(2)}`}</p>
            </article>
          ))}
        </div>
      </section>

      <section>
        <h2>Probabilities</h2>
        <div className="stat-grid">
          <div className="stat-card"><span>Above Spot</span><strong>{Math.round(props.probabilityUp * 100)}%</strong></div>
          <div className="stat-card"><span>Up 5%</span><strong>{Math.round(props.probabilityUp5 * 100)}%</strong></div>
          <div className="stat-card"><span>Up 10%</span><strong>{Math.round(props.probabilityUp10 * 100)}%</strong></div>
          <div className="stat-card"><span>Down 5%</span><strong>{Math.round(props.probabilityDown5 * 100)}%</strong></div>
          <div className="stat-card"><span>Down 10%</span><strong>{Math.round(props.probabilityDown10 * 100)}%</strong></div>
        </div>
      </section>

      <section>
        <h2>Replay Results</h2>
        <div className="stat-grid replay-grid">
          <div className="stat-card"><span>Realized Return</span><strong>{formatPct(props.replaySummary.realizedReturnPct)}</strong></div>
          <div className="stat-card"><span>Max Drawdown</span><strong>{formatPct(props.replaySummary.maxDrawdownPct)}</strong></div>
          <div className="stat-card"><span>Inside 10-90 Band</span><strong>{props.replaySummary.endedInsideOuterBand === null ? "n/a" : props.replaySummary.endedInsideOuterBand ? "Yes" : "No"}</strong></div>
          <div className="stat-card"><span>Inside 25-75 Band</span><strong>{props.replaySummary.endedInsideInnerBand === null ? "n/a" : props.replaySummary.endedInsideInnerBand ? "Yes" : "No"}</strong></div>
          <div className="stat-card replay-wide"><span>Median Path Error</span><strong>{formatPct(props.replaySummary.medianErrorPct)}</strong></div>
        </div>
      </section>

      <section>
        <h2>Value Line</h2>
        <div className="stat-grid replay-grid">
          <div className="stat-card"><span>Signal</span><strong>{props.valueLineSummary?.signal ?? "unavailable"}</strong></div>
          <div className="stat-card"><span>Fair Value</span><strong>{props.valueLineSummary?.fair_value === null || props.valueLineSummary?.fair_value === undefined ? "n/a" : props.valueLineSummary.fair_value.toFixed(2)}</strong></div>
          <div className="stat-card"><span>Upside To Value</span><strong>{formatPct(props.valueLineSummary?.upside_pct ?? null)}</strong></div>
          <div className="stat-card"><span>Price Vs Value</span><strong>{formatPct(props.valueLineSummary?.price_vs_value_pct ?? null)}</strong></div>
          <div className="stat-card replay-wide"><span>Active Models</span><strong>{props.valueLineSummary?.active_models ?? 0}</strong></div>
        </div>
      </section>

      <section>
        <h2>Scenarios</h2>
        <div className="scenario-list">
          {props.scenarios.map((scenario) => (
            <article className="scenario-card" key={scenario.name}>
              <div className="scenario-head">
                <span>{scenario.name}</span>
                <strong>{Math.round(scenario.probability * 100)}%</strong>
              </div>
              <p>{scenario.description}</p>
            </article>
          ))}
        </div>
      </section>

      <section>
        <h2>Providers</h2>
        <div className="provider-list">
          {props.providers &&
            Object.entries(props.providers).map(([name, provider]) => (
              <div className="provider-row" key={name}>
                <span>{name}</span>
                <strong>{provider.selected}</strong>
              </div>
            ))}
        </div>
      </section>
    </aside>
  );
}
