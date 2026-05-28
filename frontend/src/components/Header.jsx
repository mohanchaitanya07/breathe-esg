const TENANTS = [
  { id: 1, label: "ACME-001" },
  { id: 2, label: "GLOBEX-002" },
];

export default function Header({ tenantId, onTenantChange }) {
  return (
    <header className="header">
      <div className="brand">
        <span className="brand-mark">◐</span>
        <span className="brand-name">Breathe ESG</span>
        <span className="brand-sub">— Review Dashboard</span>
      </div>

      <label className="tenant-picker">
        <span>Tenant</span>
        <select
          value={tenantId}
          onChange={(e) => onTenantChange(Number(e.target.value))}
        >
          {TENANTS.map((t) => (
            <option key={t.id} value={t.id}>
              {t.label}
            </option>
          ))}
        </select>
      </label>
    </header>
  );
}
