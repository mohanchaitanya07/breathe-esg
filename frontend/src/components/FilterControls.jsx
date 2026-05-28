const SOURCES = ["ALL", "SAP", "UTILITY", "TRAVEL"];
const STATUSES = ["ALL", "CLEAN", "FLAGGED", "APPROVED", "REJECTED"];

export default function FilterControls({ source, status, onChange }) {
  return (
    <div className="filters">
      <label>
        <span>Source</span>
        <select
          value={source}
          onChange={(e) => onChange({ source: e.target.value, status })}
        >
          {SOURCES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </label>
      <label>
        <span>Status</span>
        <select
          value={status}
          onChange={(e) => onChange({ source, status: e.target.value })}
        >
          {STATUSES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </label>
    </div>
  );
}
