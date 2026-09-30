import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiService } from '../services/apiService';
import { DecisionBadge } from '../components/common/Badges';
import { DEMO_COMPONENT_RESULTS } from '../data/demoFallbacks';

export default function ComponentsList() {
  const navigate = useNavigate();
  const [components, setComponents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      try {
        const data = await apiService.getComponents();
        setComponents(data.results || []);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading) return <div className="p-8 animate-fade-in"><div className="text-text-muted font-medium">Loading components...</div></div>;

  const displayComponents = (components && components.length > 0) ? components : DEMO_COMPONENT_RESULTS;

  return (
    <div className="max-w-[1200px] mx-auto animate-fade-in p-4 md:p-8">
      <h1 className="text-2xl font-bold mb-4 tracking-tight text-text-primary uppercase">Components List</h1>
      <div className="card overflow-hidden">
        <div className="w-full overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th>Component ID</th>
                <th>Lot ID</th>
                <th>Device Type</th>
                <th>A_SCORE</th>
                <th>Decision</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {displayComponents.map(comp => (
                <tr key={comp.component_id} className="hover:bg-bg-surface-alt transition-colors">
                  <td className="font-mono text-accent-primary font-bold cursor-pointer" onClick={() => navigate(`/components/${comp.component_id}/explainability`)}>{comp.component_id}</td>
                  <td className="font-mono">{comp.lot || 'N/A'}</td>
                  <td>{comp.device_type || 'N/A'}</td>
                  <td className="font-mono font-semibold">{comp.a_score ?? 'N/A'}</td>
                  <td><DecisionBadge decision={comp.decision} /></td>
                  <td>
                    <button
                      onClick={() => navigate(`/components/${comp.component_id}/explainability`)}
                      className="px-2.5 py-1 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded shadow-sm transition-colors"
                    >
                      Explain & QA Report
                    </button>
                  </td>
                </tr>
              ))}
              {displayComponents.length === 0 && (
                <tr><td colSpan="6" className="text-center p-8 text-text-muted italic text-[13px]">No components found.</td></tr>
              )}

            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
