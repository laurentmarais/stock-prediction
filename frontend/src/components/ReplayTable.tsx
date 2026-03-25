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

type Props = {
  anchorPrice: number | null;
  forecast: ForecastPoint[];
  realizedPath: RealizedPoint[];
};

function pct(base: number, value: number): string {
  const result = ((value / base) - 1) * 100;
  const rounded = result.toFixed(1);
  return `${result > 0 ? "+" : ""}${rounded}%`;
}

function bandStatus(realized: number, point: ForecastPoint): string {
  if (realized >= point.p25 && realized <= point.p75) {
    return "Inside 25-75";
  }
  if (realized >= point.p10 && realized <= point.p90) {
    return "Inside 10-90";
  }
  return "Outside 10-90";
}

export function ReplayTable({ anchorPrice, forecast, realizedPath }: Props) {
  const checkpoints = [5, 10, 20];

  return (
    <section className="replay-table-wrap">
      <div className="replay-table-head">
        <h2>Replay Checkpoints</h2>
        <p>Compare realized closes against the model bands at fixed bar horizons.</p>
      </div>
      <table className="replay-table">
        <thead>
          <tr>
            <th>Bars</th>
            <th>Realized</th>
            <th>Median</th>
            <th>10-90 Band</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {checkpoints.map((checkpoint) => {
            const realized = realizedPath[checkpoint - 1];
            const point = forecast[checkpoint - 1];
            if (!anchorPrice || !realized || !point) {
              return (
                <tr key={checkpoint}>
                  <td>{checkpoint}</td>
                  <td colSpan={4}>n/a</td>
                </tr>
              );
            }
            return (
              <tr key={checkpoint}>
                <td>{checkpoint}</td>
                <td>{pct(anchorPrice, realized.value)}</td>
                <td>{pct(anchorPrice, point.p50)}</td>
                <td>{`${pct(anchorPrice, point.p10)} to ${pct(anchorPrice, point.p90)}`}</td>
                <td>{bandStatus(realized.value, point)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </section>
  );
}