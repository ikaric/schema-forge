import type { LogEntry } from "../api/types";

function shortTime(ts: string): string {
  const m = ts.match(/T(\d{2}:\d{2}:\d{2})/);
  return m ? m[1] : ts;
}

export function StatusFeed({ log }: { log: LogEntry[] }) {
  return (
    <section className="card feed">
      <h3>Activity</h3>
      <ul className="log">
        {log.map((e, i) => (
          <li key={i} className={`log-${e.level}`}>
            <span className="log-time">{shortTime(e.ts)}</span>
            <span className="log-source">{e.source}</span>
            <span className="log-msg">{e.message}</span>
          </li>
        ))}
        {log.length === 0 && <li className="muted">No activity yet.</li>}
      </ul>
    </section>
  );
}
