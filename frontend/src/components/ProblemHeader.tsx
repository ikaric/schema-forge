import type { CurrentResult, Problem } from "../api/types";

const STATUS_LABEL: Record<string, string> = {
  verified: "Verified",
  converged: "Converged",
  failed: "Failed",
};

export function ProblemHeader({
  problem,
  initialized,
  current,
}: {
  problem: Problem;
  initialized: boolean;
  current?: CurrentResult;
}) {
  if (!initialized) {
    return (
      <section className="card problem">
        <h2 className="problem-title">No circuit targeted yet</h2>
        <p className="muted">
          Run <code>/target</code> in Claude Code (or <code>make seed-example</code>)
          to define a circuit and its target spec. This view updates live as the
          harness works.
        </p>
      </section>
    );
  }
  return (
    <section className="card problem">
      <div className="problem-head">
        <h2 className="problem-title">{problem.title || "Untitled circuit"}</h2>
        <div className="chips">
          {problem.domain && <span className="chip">{problem.domain}</span>}
          {problem.tier && <span className="chip">{problem.tier}</span>}
          {current && (
            <span className={`chip status-${current.status}`}>
              {STATUS_LABEL[current.status] ?? current.status}
            </span>
          )}
        </div>
      </div>
      {problem.statement && (
        <p className="problem-statement">{problem.statement}</p>
      )}
    </section>
  );
}
