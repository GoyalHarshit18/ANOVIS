import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import AppLayout from './components/layout/AppLayout';
import Dashboard from './pages/Dashboard';
import PredictiveAnalysis from './pages/PredictiveAnalysis';
import RiskFusion from './pages/RiskFusion';
import ComponentsList from './pages/ComponentsList';
import Anomaly from './pages/Anomaly';
import Explainability from './pages/Explainability';

function App() {
  return (
    <Routes>
      <Route path="/" element={<AppLayout />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="screening" element={<Anomaly />} />
        <Route path="anomaly" element={<Anomaly />} />
        <Route path="explainability" element={<Explainability />} />
        <Route path="components/:componentId/explainability" element={<Explainability />} />
        <Route path="components/:componentId/prediction" element={<PredictiveAnalysis />} />
        <Route path="components/:componentId/risk-fusion" element={<RiskFusion />} />
        <Route path="components" element={<ComponentsList />} />
      </Route>
    </Routes>
  );
}


export default App;
