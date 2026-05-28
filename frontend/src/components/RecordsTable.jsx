import { useState } from "react";
import { approveRecord, rejectRecord } from "../api";
import { activityLabel, formatCO2e, visualState } from "../labels";
import StatusPill from "./StatusPill";

export default function RecordsTable({ records, onChanged }) {
  const [expanded, setExpanded] = useState(() => new Set());

  function toggle(id) {
    setExpanded((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }

  if (!records.length) {
    return (
      <div className="empty">
        No records for this tenant / filter combination yet. Upload a CSV above
        to populate the table.
      </div>
    );
  }

  return (
    <div className="table-wrap">
      <table className="records">
        <thead>
          <tr>
            <th aria-label="expand" />
            <th>Source</th>
            <th>Activity</th>
            <th>Scope</th>
            <th>Date</th>
            <th>Emissions</th>
            <th>Status</th>
            <th>Flag reason</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {records.map((r) => (
            <Row
              key={r.id}
              record={r}
              isOpen={expanded.has(r.id)}
              onToggle={() => toggle(r.id)}
              onChanged={onChanged}
            />
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Row({ record, isOpen, onToggle, onChanged }) {
  const [busy, setBusy] = useState(false);
  const state = visualState(record);

  async function doAction(fn) {
    setBusy(true);
    try {
      await fn(record.id);
      onChanged?.();
    } catch (err) {
      alert(err.message); 
    } finally {
      setBusy(false);
    }
  }

  const rejected = state === "rejected";
  const locked = record.is_locked;

  return (
    <>
      <tr className={`row-${state}`}>
        <td>
          <button className="toggle" onClick={onToggle} aria-label="expand row">
            {isOpen ? "▾" : "▸"}
          </button>
        </td>
        <td>{record.source}</td>
        <td className={rejected ? "struck" : ""}>{activityLabel(record)}</td>
        <td>S{record.scope}</td>
        <td>{record.activity_date}</td>
        <td>{formatCO2e(record.co2e_kg)}</td>
        <td>
          <StatusPill state={state} />
        </td>
        <td className="reason">{record.flag_reason || ""}</td>
        <td className="actions">
          {/* Hide actions for already-decided rows (locked = approved, or rejected). */}
          {!locked && !rejected && (
            <>
              <button
                className="btn btn-approve"
                disabled={busy}
                onClick={() => doAction(approveRecord)}
              >
                Approve
              </button>
              <button
                className="btn btn-reject"
                disabled={busy}
                onClick={() => doAction(rejectRecord)}
              >
                Reject
              </button>
            </>
          )}
          {locked && <span className="muted">locked</span>}
        </td>
      </tr>

      {isOpen && (
        <tr className="raw-row">
          <td />
          <td colSpan={8}>
            <div className="raw-block">
              <div className="raw-title">
                Original CSV row — batch #{record.batch_id}, row{" "}
                {record.raw_row_number}
              </div>
              <pre>{JSON.stringify(record.raw_data, null, 2)}</pre>
            </div>
          </td>
        </tr>
      )}
    </>
  );
}
