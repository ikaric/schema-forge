import type { FeedbackNote } from "../api/types";

// Live feedback loop: a note (from you or the critic) drives another /solve pass.
// Notes are parsed from design/feedback.md; `/feedback <file.md>` ingests + iterates.
export function Feedback({ feedback }: { feedback: FeedbackNote[] }) {
  const live = feedback.length > 0;
  return (
    <section className="card feedback">
      <h3>
        Feedback <span className="muted small">{live ? "live" : "ready"}</span>
      </h3>
      {live ? (
        <ul className="fb-list">
          {feedback.map((n, i) => (
            <li key={i} className={`fb fb-${n.state}`}>
              <span className="fb-from">{n.from}</span>
              <span className="fb-msg">{n.msg}</span>
              {n.status && (
                <span className={`fb-status fb-${n.state}`}>{n.status}</span>
              )}
            </li>
          ))}
        </ul>
      ) : (
        <p className="muted small fb-empty">
          No feedback yet. Write your notes in a markdown file and run{" "}
          <code>/feedback &lt;file.md&gt;</code> — each note re-runs{" "}
          <code>/solve</code> to address it.
        </p>
      )}
      <input
        className="fb-input"
        disabled
        placeholder="Notes → a .md file → /feedback <file.md>…"
      />
      <p className="muted small fb-note">
        Each ingested note re-runs <code>/solve</code> with the feedback; the new
        pass shows up in Activity, and the note closes when it's addressed.
      </p>
    </section>
  );
}
