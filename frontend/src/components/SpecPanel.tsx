import type { CurrentResult, Spec } from "../api/types";

function fmtTarget(op: string, target: number | number[], unit: string): string {
  if (Array.isArray(target)) return `${target[0]}–${target[1]} ${unit}`.trim();
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
    <section className="card spec">
      <h3>
        Spec vs measured
        {results && (
          <span className="muted">
            {nPass}/{results.length} pass
          </span>
        )}
      </h3>
      {results ? (
        <div className="speclist">
          {results.map((a) => (
            <div key={a.id} className={`spec-row ${a.passed ? "pass" : "fail"}`}>
              <div className="spec-row-head">
                <span className="mark">{a.passed ? "✓" : "✗"}</span>
                <span className="spec-id">{a.id}</span>
                <span className="spec-measured">
                  {fmtMeasured(a.measured, a.unit)}
                </span>
              </div>
              <div className="spec-row-sub">
                <span className="desc">{a.desc}</span>
                <span className="spec-target">
                  {fmtTarget(a.op, a.target, a.unit)}
                </span>
              </div>
            </div>
          ))}
        </div>
      ) : spec ? (
        <div className="speclist">
          {spec.assertions.map((a) => (
            <div key={a.id} className="spec-row">
              <div className="spec-row-head">
                <span className="spec-id">{a.id}</span>
                <span className="spec-target">
                  {fmtTarget(a.op, a.target, a.unit)}
                </span>
              </div>
              {a.desc && (
                <div className="spec-row-sub">
                  <span className="desc">{a.desc}</span>
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <p className="muted">No spec yet.</p>
      )}
    </section>
  );
}
