import React, { useEffect } from "react";

export default function SlideOver({ open, title, onClose, children }) {
  useEffect(() => {
    if (!open) return;

    const onKeyDown = (e) => {
      if (e.key === "Escape") onClose?.();
    };

    document.addEventListener("keydown", onKeyDown);
    document.body.style.overflow = "hidden";

    return () => {
      document.removeEventListener("keydown", onKeyDown);
      document.body.style.overflow = "";
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 9999,
        display: "flex",
        justifyContent: "flex-end",
      }}
      aria-modal="true"
      role="dialog"
    >
      <div
        onClick={onClose}
        style={{
          position: "absolute",
          inset: 0,
          background: "rgba(0,0,0,0.35)",
        }}
      />

      <div
        style={{
          position: "relative",
          width: "520px",
          maxWidth: "92vw",
          height: "100%",
          background: "white",
          boxShadow: "0 10px 30px rgba(0,0,0,0.25)",
          display: "flex",
          flexDirection: "column",
        }}
      >
        <div
          style={{
            padding: "14px 16px",
            borderBottom: "1px solid rgba(0,0,0,0.08)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: 10,
          }}
        >
          <div style={{ fontWeight: 700, fontSize: 16 }}>{title || "Details"}</div>
          <button 
            onClick={onClose} 
            aria-label="Close"
            style={{
              background: "none",
              border: "none",
              fontSize: 18,
              cursor: "pointer",
              padding: "4px 8px",
              borderRadius: 4,
            }}
          >
            ✕
          </button>
        </div>

        <div style={{ padding: 16, overflow: "auto", flex: 1 }}>{children}</div>
      </div>
    </div>
  );
}
