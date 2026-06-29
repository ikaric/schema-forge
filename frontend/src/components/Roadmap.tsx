import type { Roadmap as RoadmapT } from "../api/types";

export function Roadmap({ roadmap }: { roadmap: RoadmapT }) {
  const { done, total } = roadmap.progress;
  const pct = total ? Math.round((done / total) * 100) : 0;
  return (
    <section className="card roadmap">
      <h3>
        Roadmap <span className="muted small">{done}/{total} verified</span>
      </h3>
      <div className="progress">
        <div className="progress-bar" style={{ width: `${pct}%` }} />
      </div>
      <ul className="checklist">
        {roadmap.subgoals.map((g, i) => (
          <li key={i} className={g.done ? "done" : ""}>
            <span className="check">{g.done ? "✓" : "○"}</span>
            {g.text}
          </li>
        ))}
        {roadmap.subgoals.length === 0 && (
          <li className="muted">No sub-goals yet.</li>
        )}
      </ul>
      {roadmap.vectors.length > 0 && (
        <>
          <h4 className="muted small">Attack vectors</h4>
          <ul className="checklist">
            {roadmap.vectors.map((v, i) => (
              <li key={i} className={v.done ? "done" : ""}>
                <span className="check">{v.done ? "✓" : "○"}</span>
                {v.text}
              </li>
            ))}
          </ul>
        </>
      )}
    </section>
  );
}
