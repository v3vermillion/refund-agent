// Colored decision badge: green=approved, red=denied, amber=escalated.
const MAP = {
  APPROVED: { label: "Approved", cls: "badge badge-approved" },
  DENIED: { label: "Denied", cls: "badge badge-denied" },
  ESCALATED: { label: "Escalated", cls: "badge badge-escalated" },
};

export default function DecisionBadge({ decision }) {
  if (!decision) return null;
  const meta = MAP[decision] || { label: decision, cls: "badge" };
  return <span className={meta.cls}>{meta.label}</span>;
}
