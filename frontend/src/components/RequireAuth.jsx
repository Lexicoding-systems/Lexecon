import React from "react";
import { Navigate, useLocation } from "react-router-dom";

export default function RequireAuth({ children }) {
  const token = localStorage.getItem("lexecon_token");
  const location = useLocation();
  
  if (!token) {
    // Redirect to login, but save where they were trying to go
    return <Navigate to="/login" state={{ from: location }} replace />;
  }
  
  return children;
}
