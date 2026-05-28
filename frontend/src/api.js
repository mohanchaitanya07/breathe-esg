const API_BASE = "/api";

export const ANALYST = "analyst@breathe";

async function asJson(res) {
  const text = await res.text();
  let body = null;
  try {
    body = text ? JSON.parse(text) : null;
  } catch {
    body = { error: text };
  }
  if (!res.ok) {
    const msg = (body && body.error) || `request failed (${res.status})`;
    const err = new Error(msg);
    err.status = res.status;
    err.body = body;
    throw err;
  }
  return body;
}

// GET /api/records/?tenant_id=&source=&status=
export async function fetchRecords({ tenantId, source, status }) {
  const params = new URLSearchParams({ tenant_id: tenantId });
  if (source && source !== "ALL") params.set("source", source);
  if (status && status !== "ALL") params.set("status", status);
  const res = await fetch(`${API_BASE}/records/?${params.toString()}`);
  return asJson(res);
}

export async function uploadCsv({ tenantId, source, file }) {
  const fd = new FormData();
  fd.append("tenant_id", tenantId);
  fd.append("source", source);
  fd.append("uploaded_by", ANALYST);
  fd.append("file", file);
  const res = await fetch(`${API_BASE}/upload/`, { method: "POST", body: fd });
  return asJson(res);
}

export async function approveRecord(id, note = "") {
  const fd = new FormData();
  fd.append("changed_by", ANALYST);
  fd.append("note", note);
  const res = await fetch(`${API_BASE}/records/${id}/approve/`, {
    method: "POST",
    body: fd,
  });
  return asJson(res);
}

export async function rejectRecord(id, note = "") {
  const fd = new FormData();
  fd.append("changed_by", ANALYST);
  fd.append("note", note);
  const res = await fetch(`${API_BASE}/records/${id}/reject/`, {
    method: "POST",
    body: fd,
  });
  return asJson(res);
}
