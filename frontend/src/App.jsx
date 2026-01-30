import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import AuditDashboard from "./components/AuditDashboard";
import Login from "./pages/Login";
import RequireAuth from "./components/RequireAuth";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/audit" replace />} />
      <Route path="/login" element={<Login />} />
      <Route
        path="/audit"
        element={
          <RequireAuth>
            <AuditDashboard />
          </RequireAuth>
        }
      />
      <Route path="*" element={<Navigate to="/audit" replace />} />
    </Routes>
  );
}
