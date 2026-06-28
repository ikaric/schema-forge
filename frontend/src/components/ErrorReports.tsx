import type { CurrentResult } from "../api/types";

export function ErrorReports({ current }: { current?: CurrentResult }) {
  if (!current) return null;
  const { errors, warnings } = current;
  if (errors.length === 0 && warnings.length === 0) return null;
  return (
    <section className="card">
      <h3>{errors.length > 0 ? "Errors" : "Warnings"}</h3>
      {errors.length > 0 && (
        <ul className="errlist">
          {errors.map((e, i) => (
            <li key={i} className="err">
              {e}
            </li>
          ))}
        </ul>
      )}
      {warnings.length > 0 && (
        <ul className="errlist">
          {warnings.slice(0, 8).map((w, i) => (
            <li key={i} className="warn">
              {w}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
