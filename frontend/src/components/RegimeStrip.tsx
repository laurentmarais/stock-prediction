type RegimePoint = {
  time: string;
  regime: string;
};

type Props = {
  currentRegime: string;
  history: RegimePoint[];
};

function regimeClass(regime: string): string {
  if (regime.includes("high-vol")) {
    return "high-vol";
  }
  if (regime.includes("low-vol")) {
    return "low-vol";
  }
  return "normal-vol";
}

export function RegimeStrip({ currentRegime, history }: Props) {
  return (
    <section className="regime-strip-wrap">
      <div className="replay-table-head">
        <h2>Regime History</h2>
        <p>Recent regime states leading into the current replay anchor.</p>
      </div>
      <div className="regime-strip-current">
        <span className="eyebrow">Current Regime</span>
        <strong>{currentRegime}</strong>
      </div>
      <div className="regime-strip">
        {history.map((point) => (
          <div className={`regime-cell ${regimeClass(point.regime)}`} key={`${point.time}-${point.regime}`} title={`${new Date(point.time).toLocaleDateString()} - ${point.regime}`}>
            <span className="regime-cell-date">{new Date(point.time).toLocaleDateString()}</span>
            <span className="regime-cell-label">{point.regime}</span>
          </div>
        ))}
      </div>
    </section>
  );
}