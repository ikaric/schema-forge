import { marked } from "marked";

// Shown until the librarian survey lands in design/research.md (or findings/lit-*.md).
const PLACEHOLDER = `**Planned.** Before drafting a circuit, the harness surveys prior art and
gathers it here in one place:

- **Similar schematics** — known topologies for this circuit class with their
  real component values and bias points.
- **Datasheets & application notes** — device models and reference circuits.
- **Reference sources** — community analyses and prior designs, cited.

Run \`/research\` after \`/target\`: the *librarian* writes the survey into
\`design/research.md\`, and it renders here — scrollable, so it's all in one place.`;

export function Research({ research }: { research: string }) {
  const live = research.trim().length > 0;
  const html = marked.parse(live ? research : PLACEHOLDER) as string;
  return (
    <section className="card research">
      <div className="bar">
        <h3>
          Research <span className="muted small">{live ? "live" : "planned"}</span>
        </h3>
      </div>
      <div
        className="research-body tb-brief"
        dangerouslySetInnerHTML={{ __html: html }}
      />
    </section>
  );
}
