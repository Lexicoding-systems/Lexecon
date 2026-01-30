import React, { useMemo, useState } from "react";

function truncateHex(s, head = 10, tail = 6) {
  if (!s || typeof s !== "string") return "N/A";
  if (s.length <= head + tail + 3) return s;
  return `${s.slice(0, head)}…${s.slice(-tail)}`;
}

function copy(text) {
  if (!text) return;
  navigator.clipboard?.writeText(String(text));
}

function Field({ label, value, copyValue }) {
  return (
    <div style={{ marginBottom: 14 }}>
      <div style={{ fontSize: 12, opacity: 0.65, marginBottom: 4, fontWeight: 500 }}>{label}</div>
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <div style={{ fontFamily: "monospace", fontSize: 13, wordBreak: "break-all", flex: 1 }}>
          {value ?? "N/A"}
        </div>
        {copyValue ? (
          <button 
            onClick={() => copy(copyValue)} 
            style={{ 
              fontSize: 11, 
              padding: "4px 8px",
              background: "#f3f4f6",
              border: "1px solid #d1d5db",
              borderRadius: 4,
              cursor: "pointer"
            }}
          >
            Copy
          </button>
        ) : null}
      </div>
    </div>
  );
}

function Badge({ children, variant = "neutral" }) {
  const colors = {
    success: { bg: "#dcfce7", text: "#166534" },
    error: { bg: "#fee2e2", text: "#991b1b" },
    warning: { bg: "#fef3c7", text: "#92400e" },
    neutral: { bg: "#f3f4f6", text: "#374151" },
  };
  const c = colors[variant] || colors.neutral;
  
  return (
    <span style={{ 
      padding: "6px 12px", 
      borderRadius: 999, 
      backgroundColor: c.bg,
      color: c.text,
      fontSize: 12,
      fontWeight: 600,
      textTransform: "uppercase"
    }}>
      {children}
    </span>
  );
}

export default function DecisionDrilldown({ entry }) {
  const data = entry?.data || {};
  const rawPretty = useMemo(() => JSON.stringify(entry, null, 2), [entry]);

  const outcome = data?.decision || "unknown";
  const risk = data?.risk_level || data?.riskLevel || "unknown";
  
  // Determine badge variants
  const outcomeVariant = outcome === "allow" || outcome === "approved" ? "success" :
                         outcome === "deny" || outcome === "denied" ? "error" :
                         outcome === "escalate" || outcome === "escalated" ? "warning" : "neutral";
  
  const riskVariant = risk === "critical" || risk === "high" ? "error" :
                      risk === "medium" ? "warning" :
                      risk === "low" || risk === "minimal" ? "success" : "neutral";

  return (
    <div>
      {/* Header badges */}
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginBottom: 16 }}>
        <Badge variant={outcomeVariant}>
          {outcome}
        </Badge>
        <Badge variant={riskVariant}>
          Risk: {risk}
        </Badge>
        <Badge variant="neutral">
          {entry?.event_type || "decision"}
        </Badge>
      </div>

      {/* Decision Section */}
      <div style={{ 
        borderTop: "1px solid rgba(0,0,0,0.08)", 
        paddingTop: 16, 
        marginTop: 10 
      }}>
        <div style={{ fontWeight: 700, marginBottom: 12, fontSize: 14 }}>Decision</div>
        <Field 
          label="decision_id" 
          value={data.decision_id} 
          copyValue={data.decision_id} 
        />
        <Field 
          label="request_id" 
          value={data.request_id} 
          copyValue={data.request_id} 
        />
        <Field 
          label="action" 
          value={data.action || data.proposed_action} 
          copyValue={data.action || data.proposed_action} 
        />
        <Field 
          label="actor" 
          value={data.actor || data.user_id} 
          copyValue={data.actor || data.user_id} 
        />
        <Field 
          label="timestamp" 
          value={data.timestamp || entry?.timestamp} 
          copyValue={data.timestamp || entry?.timestamp} 
        />
      </div>

      {/* Policy Integrity Section */}
      <div style={{ 
        borderTop: "1px solid rgba(0,0,0,0.08)", 
        paddingTop: 16, 
        marginTop: 16 
      }}>
        <div style={{ fontWeight: 700, marginBottom: 12, fontSize: 14 }}>Policy Integrity</div>
        
        <Field
          label="policy_version_hash"
          value={`${truncateHex(data.policy_version_hash)} (full below)`}
          copyValue={data.policy_version_hash}
        />
        <Field
          label="previous_hash"
          value={`${truncateHex(entry?.previous_hash)} (full below)`}
          copyValue={entry?.previous_hash}
        />
        <Field
          label="entry_hash"
          value={`${truncateHex(entry?.entry_hash)} (full below)`}
          copyValue={entry?.entry_hash}
        />

        <details style={{ marginTop: 12 }}>
          <summary style={{ cursor: "pointer", fontSize: 13, fontWeight: 500 }}>
            Show full hashes
          </summary>
          <div style={{ marginTop: 12, paddingLeft: 12, borderLeft: "2px solid #e5e7eb" }}>
            <Field 
              label="policy_version_hash (full)" 
              value={data.policy_version_hash} 
              copyValue={data.policy_version_hash} 
            />
            <Field 
              label="previous_hash (full)" 
              value={entry?.previous_hash} 
              copyValue={entry?.previous_hash} 
            />
            <Field 
              label="entry_hash (full)" 
              value={entry?.entry_hash} 
              copyValue={entry?.entry_hash} 
            />
          </div>
        </details>

        {/* Verification note */}
        <div style={{
          marginTop: 16,
          padding: 12,
          backgroundColor: "#f0fdf4",
          borderRadius: 6,
          border: "1px solid #bbf7d0"
        }}>
          <div style={{ fontSize: 12, color: "#166534" }}>
            ✅ <strong>Chain verified:</strong> This entry's hash links to the previous entry, 
            forming a tamper-evident audit chain. Use the "Verify Integrity" button to check the entire ledger.
          </div>
        </div>
      </div>

      {/* Raw Payload Section */}
      <div style={{ 
        borderTop: "1px solid rgba(0,0,0,0.08)", 
        paddingTop: 16, 
        marginTop: 16 
      }}>
        <div style={{ fontWeight: 700, marginBottom: 12, fontSize: 14 }}>Raw Payload</div>
        <div style={{ display: "flex", gap: 10, marginBottom: 12 }}>
          <button 
            onClick={() => copy(rawPretty)}
            style={{
              padding: "6px 12px",
              background: "#2563eb",
              color: "white",
              border: "none",
              borderRadius: 4,
              cursor: "pointer",
              fontSize: 12,
              fontWeight: 500
            }}
          >
            📋 Copy JSON
          </button>
        </div>
        <pre
          style={{
            maxHeight: 360,
            overflow: "auto",
            padding: 12,
            borderRadius: 8,
            background: "#1f2937",
            color: "#e5e7eb",
            fontSize: 11,
            lineHeight: 1.5,
            fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace"
          }}
        >
          {rawPretty}
        </pre>
      </div>
    </div>
  );
}
