import { marked } from "marked";
import type { CurrentResult, Problem } from "../api/types";

const STAMP: Record<string, string> = {
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
      <section className="titleblock">
        <div className="tb-main">
          <p className="eyebrow">Untargeted sheet</p>
          <h2 className="tb-name">No circuit targeted</h2>
          <p className="tb-brief">
            Run <code>/target</code> to define a circuit and its target spec.
            This sheet updates live as the harness designs and verifies it.
          </p>
        </div>
      </section>
    );
  }

  const status = current?.status;
  const passed = current?.assertions.filter((a) => a.passed).length ?? 0;
  const total = current?.assertions.length ?? 0;
  // The statement is authored markdown — render it (trusted, local content).
  // No `breaks`: let hard-wrapped source lines reflow into justified blocks.
  const briefHtml = problem.statement
    ? (marked.parse(problem.statement) as string)
    : "";

  return (
    <section className="titleblock">
      <div className="tb-main">
        <p className="eyebrow">Circuit under design</p>
        <h2 className="tb-name">{problem.title || "Untitled circuit"}</h2>
        <div className="tb-chips">
          {problem.domain && <span className="chip">{problem.domain}</span>}
          {problem.tier && <span className="chip">{problem.tier}</span>}
        </div>
        {briefHtml && (
          <div
            className="tb-brief"
            dangerouslySetInnerHTML={{ __html: briefHtml }}
          />
        )}
      </div>
      {status && (
        <div className={`stamp s-${status}`}>
          {STAMP[status] ?? status}
          <small>
            spec {passed}/{total}
          </small>
        </div>
      )}
    </section>
  );
}
