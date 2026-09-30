/**
 * Centralized API Client for Anovis Frontend.
 * Supports configurable VITE_API_BASE_URL for Vercel <-> Render production deployment.
 */
export const API_BASE = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '');

export const apiService = {
  getHealth: async () => {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error('Health check failed');
    return res.json();
  },

  getReadiness: async () => {
    const res = await fetch(`${API_BASE}/health/ready`);
    if (!res.ok) throw new Error('Readiness check failed');
    return res.json();
  },

  getModelInfo: async () => {
    const res = await fetch(`${API_BASE}/model-info`);
    if (!res.ok) throw new Error('Model info failed');
    return res.json();
  },

  predictUnified: async (payload) => {
    const res = await fetch(`${API_BASE}/api/predict`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error('Unified prediction failed');
    return res.json();
  },

  screenComponent: async (payload) => {
    const res = await fetch(`${API_BASE}/screen`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error('Screening failed');
    return res.json();
  },

  batchScreen: async (fileOrRecords, onProgress = null) => {
    let body;
    let headers = {};
    
    if (fileOrRecords instanceof File) {
      const formData = new FormData();
      formData.append('file', fileOrRecords);
      body = formData;
    } else {
      const formData = new FormData();
      const payload = Array.isArray(fileOrRecords) ? fileOrRecords : [];
      formData.append('records', JSON.stringify(payload));
      body = formData;
    }

    if (onProgress) onProgress('Ingesting & validating dataset...');
    const res = await fetch(`${API_BASE}/upload`, {
      method: 'POST',
      headers,
      body
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail?.message || err.message || 'Dataset upload failed');
    }
    const uploadData = await res.json();
    const runId = uploadData.run_id;

    // Run ML Pipeline
    if (onProgress) onProgress('Running Module A (PAT & Peer)...');
    const resA = await fetch(`${API_BASE}/screening-runs/${runId}/module-a`, { method: 'POST' });
    if (!resA.ok) {
      const err = await resA.json().catch(() => ({}));
      throw new Error(err.detail?.message || 'Module A execution failed');
    }

    if (onProgress) onProgress('Running Anomaly Analysis...');
    const resAnom = await fetch(`${API_BASE}/screening-runs/${runId}/anomaly-analysis`, { method: 'POST' });
    if (!resAnom.ok) {
      const err = await resAnom.json().catch(() => ({}));
      throw new Error(err.detail?.message || 'Anomaly analysis failed');
    }

    if (onProgress) onProgress('Running Predictive Modeling (Module B)...');
    const resB = await fetch(`${API_BASE}/screening-runs/${runId}/module-b`, { method: 'POST' });
    if (!resB.ok) {
      const err = await resB.json().catch(() => ({}));
      throw new Error(err.detail?.message || 'Module B predictive modeling failed');
    }

    if (onProgress) onProgress('Executing Risk Fusion Engine...');
    const resRF = await fetch(`${API_BASE}/screening-runs/${runId}/risk-fusion`, { method: 'POST' });
    if (!resRF.ok) {
      const err = await resRF.json().catch(() => ({}));
      throw new Error(err.detail?.message || 'Risk fusion failed');
    }

    // Fetch the updated components to get the summary and results
    if (onProgress) onProgress('Loading final component decisions...');
    const compRes = await fetch(`${API_BASE}/components`);
    if (!compRes.ok) throw new Error('Failed to fetch updated components');
    const compData = await compRes.json();

    return {
      run_id: runId,
      summary: compData.summary || {},
      results: compData.results || []
    };
  },

  getComponent: async (componentId) => {
    const res = await fetch(`${API_BASE}/component/${componentId}`);
    if (!res.ok) throw new Error('Component not found');
    return res.json();
  },

  getComponents: async (lotId = null) => {
    const url = lotId ? `${API_BASE}/components?lot_id=${encodeURIComponent(lotId)}` : `${API_BASE}/components`;
    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to load components');
    return res.json();
  },

  getLots: async () => {
    const res = await fetch(`${API_BASE}/lots`);
    if (!res.ok) throw new Error('Failed to load lots');
    return res.json();
  },

  getLot: async (lotId) => {
    const res = await fetch(`${API_BASE}/lot/${lotId}`);
    if (!res.ok) throw new Error('Lot not found');
    return res.json();
  },

  // Module 3 API Functions
  getGlobalExplainability: async () => {
    const res = await fetch(`${API_BASE}/api/explainability/global`);
    if (!res.ok) throw new Error('Failed to load global SHAP explainability');
    return res.json();
  },

  getComponentExplainability: async (componentId, measurements = null) => {
    const res = await fetch(`${API_BASE}/api/explainability/component`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ component_id: componentId, measurements })
    });
    if (!res.ok) throw new Error('Failed to compute component explanation');
    return res.json();
  },

  generateQAReport: async (componentId, measurements = null) => {
    const res = await fetch(`${API_BASE}/api/reports/qa`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ component_id: componentId, measurements })
    });
    if (!res.ok) throw new Error('Failed to generate Gemini QA report');
    return res.json();
  },

  getPDFDownloadUrl: (componentId) => {
    return `${API_BASE}/api/reports/qa/${componentId}/pdf`;
  },

  getScreeningRunExportUrl: (runId, type) => {
    return `${API_BASE}/screening-runs/${runId}/export/${type}`;
  }
};
