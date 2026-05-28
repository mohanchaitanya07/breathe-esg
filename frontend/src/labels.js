function fmt(n) {
  if (n === null || n === undefined || Number.isNaN(n)) return "—";
  if (Math.abs(n) >= 100) return Math.round(n).toLocaleString();
  return n.toFixed(1);
}

export function activityLabel(record) {
  const { source, activity_value, activity_unit, raw_data: raw = {} } = record;
  const value = fmt(activity_value);
  const unit = activity_unit || "";

  if (source === "SAP") {
    const what = raw.Short_Text || raw.Material || "Item";
    return `${what} — ${value} ${unit}`.trim();
  }
  if (source === "UTILITY") {
    const acct = raw.Account_No ? `Account ${raw.Account_No}` : "Electricity";
    return `${acct} — ${value} ${unit}`.trim();
  }
  if (source === "TRAVEL") {
    const t = raw.Type || "Travel";
    const desc = raw.Description || "";
    return `${t}${desc ? " " + desc : ""} — ${value} ${unit}`.trim();
  }
  return `${value} ${unit}`.trim();
}

export function visualState(record) {
  const s = record.review_status;
  if (s === "APPROVED") return "approved";
  if (s === "REJECTED") return "rejected";
  if (s === "CLEAN") return "clean";
  const reason = (record.flag_reason || "").toLowerCase();
  if (reason.includes("mvp scope")) return "out_of_scope";
  return "needs_review";
}

export const VISUAL_LABEL = {
  clean: "Ready",
  needs_review: "Needs review",
  out_of_scope: "Out of scope (known)",
  approved: "Approved / Locked",
  rejected: "Rejected",
};

export function formatCO2e(value) {
  if (value === null || value === undefined) return "—";
  return `${fmt(value)} kg`;
}
