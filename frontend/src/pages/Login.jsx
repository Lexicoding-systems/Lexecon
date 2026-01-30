import React, { useState, useEffect } from "react";
import { AuthAPI } from "../api/endpoints";

export default function Login() {
  const [token, setToken] = useState(localStorage.getItem("lexecon_token") || "");
  const [tenantId, setTenantId] = useState(
    localStorage.getItem("lexecon_tenant_id") ||
      process.env.REACT_APP_DEFAULT_TENANT_ID ||
      "default"
  );
  const [status, setStatus] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  // Check if already authenticated
  useEffect(() => {
    const checkAuth = async () => {
      const existingToken = localStorage.getItem("lexecon_token");
      if (existingToken) {
        try {
          const res = await AuthAPI.me();
          setStatus(`✅ Already authenticated as: ${res?.data?.user?.email || "user"}`);
          // Optional: auto-redirect if already logged in
          // window.location.href = "/audit";
        } catch (e) {
          // Token invalid, clear it
          localStorage.removeItem("lexecon_token");
        }
      }
    };
    checkAuth();
  }, []);

  const save = async () => {
    setIsLoading(true);
    setStatus("Validating…");
    
    const trimmedToken = token.trim();
    if (!trimmedToken) {
      setStatus("❌ Please enter a token");
      setIsLoading(false);
      return;
    }

    localStorage.setItem("lexecon_token", trimmedToken);
    localStorage.setItem("lexecon_tenant_id", (tenantId.trim() || "default"));

    try {
      const res = await AuthAPI.me();
      setStatus(`✅ Auth OK: ${res?.data?.user?.email || res?.data?.user?.username || "user"}`);
      // Small delay so user sees success message
      setTimeout(() => {
        window.location.href = "/audit";
      }, 500);
    } catch (e) {
      setStatus(`❌ Auth failed: ${e.message}`);
      localStorage.removeItem("lexecon_token");
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") {
      save();
    }
  };

  return (
    <div style={{ 
      minHeight: "100vh", 
      display: "flex", 
      alignItems: "center", 
      justifyContent: "center",
      backgroundColor: "#f3f4f6"
    }}>
      <div style={{ 
        padding: 32, 
        maxWidth: 480, 
        width: "100%",
        backgroundColor: "white",
        borderRadius: 8,
        boxShadow: "0 1px 3px rgba(0,0,0,0.1)"
      }}>
        <h2 style={{ marginTop: 0, marginBottom: 8 }}>Lexecon Login</h2>
        <p style={{ color: "#6b7280", marginBottom: 24, fontSize: 14 }}>
          Paste your session_id from <code>/auth/login</code> to authenticate.
        </p>

        <div style={{ marginBottom: 16 }}>
          <label style={{ 
            display: "block", 
            marginBottom: 6, 
            fontSize: 14, 
            fontWeight: 500,
            color: "#374151"
          }}>
            Tenant ID
          </label>
          <input
            value={tenantId}
            onChange={(e) => setTenantId(e.target.value)}
            onKeyDown={handleKeyDown}
            style={{ 
              width: "100%", 
              padding: "10px 12px", 
              borderRadius: 6,
              border: "1px solid #d1d5db",
              fontSize: 14,
              boxSizing: "border-box"
            }}
            placeholder="default"
          />
        </div>

        <div style={{ marginBottom: 24 }}>
          <label style={{ 
            display: "block", 
            marginBottom: 6, 
            fontSize: 14, 
            fontWeight: 500,
            color: "#374151"
          }}>
            Token (session_id)
          </label>
          <textarea
            value={token}
            onChange={(e) => setToken(e.target.value)}
            onKeyDown={handleKeyDown}
            style={{ 
              width: "100%", 
              padding: "10px 12px", 
              borderRadius: 6,
              border: "1px solid #d1d5db",
              fontSize: 14,
              minHeight: 100,
              boxSizing: "border-box",
              fontFamily: "monospace"
            }}
            placeholder="Paste session_id here..."
          />
        </div>

        <button 
          onClick={save} 
          disabled={isLoading}
          style={{ 
            width: "100%",
            padding: "12px 16px",
            backgroundColor: isLoading ? "#9ca3af" : "#2563eb",
            color: "white",
            border: "none",
            borderRadius: 6,
            fontSize: 14,
            fontWeight: 500,
            cursor: isLoading ? "not-allowed" : "pointer"
          }}
        >
          {isLoading ? "Validating…" : "Sign In"}
        </button>

        {status && (
          <div style={{ 
            marginTop: 16, 
            padding: 12,
            borderRadius: 6,
            backgroundColor: status.startsWith("✅") ? "#dcfce7" : 
                            status.startsWith("❌") ? "#fee2e2" : "#f3f4f6",
            color: status.startsWith("✅") ? "#166534" : 
                   status.startsWith("❌") ? "#991b1b" : "#374151",
            fontSize: 14
          }}>
            {status}
          </div>
        )}

        <div style={{ marginTop: 24, paddingTop: 16, borderTop: "1px solid #e5e7eb" }}>
          <p style={{ fontSize: 12, color: "#6b7280", margin: 0 }}>
            <strong>How to get a token:</strong>
          </p>
          <ol style={{ fontSize: 12, color: "#6b7280", margin: "8px 0 0 0", paddingLeft: 16 }}>
            <li>Run <code>curl -X POST http://localhost:8000/auth/login -d '{"username":"...","password":"..."}'</code></li>
            <li>Copy the <code>session_id</code> from the response</li>
            <li>Paste it above</li>
          </ol>
        </div>
      </div>
    </div>
  );
}
