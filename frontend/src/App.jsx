import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuditDashboard } from './components/AuditDashboard';

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50">
        <Routes>
          <Route path="/" element={<Navigate to="/audit" replace />} />
          <Route path="/audit" element={<AuditDashboard />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
