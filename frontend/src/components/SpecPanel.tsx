import type { CurrentResult, Spec } from "../api/types";

function fmtTarget(op: string, target: number | number[], unit: string): string {
  if (Array.isArray(target)) return `${target[0]} … ${target[1]} ${unit}`.trim();
  return `${op} ${target} ${unit}`.trim();
}

function fmtMeasured(value: number | null, unit: string): string {
  if (value === null) return "—";
  return `${Number(value.toPrecision(4))} ${unit}`.trim();
}

export function SpecPanel({
  current,
  spec,
}: {
  current?: CurrentResult;
  spec: Spec | null;
}) {
  const results = current?.assertions;
  const nPass = results ? results.filter((a) => a.passed).length : 0;
  return (
    <section className="card">
      <h3>
        Spec vs measured{" "}
        {results && (
          <span className="muted small">
            {nPass}/{results.length} pass
          </span>
        )}
      </h3>
      {results ? (
        <table className="spec-table">
          <thead>
            <tr>
              <th />
              <th>Check</th>
              <th>Measured</th>
              <th>Target</th>
            </tr>
          </thead>
          <tbody>
            {results.map((a) => (
              <tr key={a.id} className={a.passed ? "pass" : "fail"}>
                <td className="mark">{a.passed ? "✓" : "✗"}</td>
                <td>
                  <div className="spec-id">{a.id}</div>
                  <div className="muted small">{a.desc}</div>
                </td>
                <td className="num">{fmtMeasured(a.measured, a.unit)}</td>
                <td className="num">{fmtTarget(a.op, a.target, a.unit)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : spec ? (
        <table className="spec-table">
          <thead>
            <tr>
              <th>Metric</th>
              <th>Target</th>
            </tr>
          </thead>
          <tbody>
            {spec.assertions.map((a) => (
              <tr key={a.id}>
                <td>
                  <div className="spec-id">{a.id}</div>
                  <div className="muted small">{a.desc}</div>
                </td>
                <td className="num">{fmtTarget(a.op, a.target, a.unit)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p className="muted">No spec yet.</p>
      )}
    </section>
  );
}
