import { visualState } from "../labels";

export default function SummaryCards({ records }) {
  const counts = {
    total: records.length,
    clean: 0,
    needs_review: 0,
    out_of_scope: 0,
    approved: 0,
    rejected: 0,
  };
  for (const r of records) {
    counts[visualState(r)] += 1;
  }

  const cards = [
    { label: "Total rows", value: counts.total, tone: "neutral" },
    { label: "Ready (clean)", value: counts.clean, tone: "good" },
    { label: "Needs review", value: counts.needs_review, tone: "warn" },
    { label: "Out of scope (known)", value: counts.out_of_scope, tone: "muted" },
    { label: "Approved / Locked", value: counts.approved, tone: "info" },
    { label: "Rejected", value: counts.rejected, tone: "bad" },
  ];

  return (
    <section className="summary-grid">
      {cards.map((c) => (
        <div key={c.label} className={`stat-card tone-${c.tone}`}>
          <div className="stat-value">{c.value}</div>
          <div className="stat-label">{c.label}</div>
        </div>
      ))}
    </section>
  );
}
