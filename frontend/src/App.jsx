import { useCallback, useEffect, useState } from "react";
import { fetchRecords } from "./api";
import Header from "./components/Header";
import UploadPanel from "./components/UploadPanel";
import SummaryCards from "./components/SummaryCards";
import FilterControls from "./components/FilterControls";
import RecordsTable from "./components/RecordsTable";
import LandingScreen from "./components/LandingScreen";

export default function App() {
  const [entered, setEntered] = useState(false);

  const [tenantId, setTenantId] = useState(1);
  const [filter, setFilter] = useState({ source: "ALL", status: "ALL" });
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchRecords({
        tenantId,
        source: filter.source,
        status: filter.status,
      });
      setRecords(data.results || []);
    } catch (err) {
      setError(err.message);
      setRecords([]);
    } finally {
      setLoading(false);
    }
  }, [tenantId, filter.source, filter.status]);

  useEffect(() => {
    if (entered) reload();
  }, [entered, reload]);

  if (!entered) {
    return <LandingScreen onEnter={() => setEntered(true)} />;
  }

  return (
    <div className="app">
      <Header tenantId={tenantId} onTenantChange={setTenantId} />

      <main className="content">
        <UploadPanel tenantId={tenantId} onUploaded={reload} />

        <section>
          <h2 className="section-title">Summary</h2>
          <SummaryCards records={records} />
        </section>

        <section>
          <div className="section-header">
            <h2 className="section-title">Review queue</h2>
            <FilterControls
              source={filter.source}
              status={filter.status}
              onChange={setFilter}
            />
          </div>

          {error && <div className="error-banner">Error: {error}</div>}
          {loading ? (
            <div className="empty">Loading…</div>
          ) : (
            <RecordsTable records={records} onChanged={reload} />
          )}
        </section>
      </main>

      <footer className="footer">
        Backend: <code>http://127.0.0.1:8000/api</code> — Tenant id {tenantId}
      </footer>
    </div>
  );
}
