import { useState } from "react";
import { uploadCsv } from "../api";

export default function UploadPanel({ tenantId, onUploaded }) {
  const [source, setSource] = useState("SAP");
  const [file, setFile] = useState(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState(null);

  async function submit(e) {
    e.preventDefault();
    if (!file) {
      setMessage({ kind: "error", text: "Please choose a CSV file first." });
      return;
    }
    setBusy(true);
    setMessage(null);
    try {
      const r = await uploadCsv({ tenantId, source, file });
      setMessage({
        kind: "ok",
        text: `Ingested ${r.total} rows: ${r.clean} clean, ${r.flagged} flagged. (Batch #${r.batch_id})`,
      });
      setFile(null);
      e.target.reset();
      onUploaded?.();
    } catch (err) {
      setMessage({ kind: "error", text: err.message });
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="card">
      <h2 className="card-title">Upload CSV</h2>
      <form className="upload-form" onSubmit={submit}>
        <label className="field">
          <span>Source</span>
          <select value={source} onChange={(e) => setSource(e.target.value)}>
            <option value="SAP">SAP (fuel + procurement)</option>
            <option value="UTILITY">Utility (electricity)</option>
            <option value="TRAVEL">Travel (flights / hotels / cars)</option>
          </select>
        </label>

        <label className="field grow">
          <span>File</span>
          <input
            type="file"
            accept=".csv"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
          />
        </label>

        <button className="btn btn-primary" type="submit" disabled={busy}>
          {busy ? "Uploading…" : "Upload"}
        </button>
      </form>

      {message && (
        <div className={`upload-message ${message.kind}`}>{message.text}</div>
      )}
    </section>
  );
}
