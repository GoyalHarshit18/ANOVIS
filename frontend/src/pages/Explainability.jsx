import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  BrainCircuit, Download, Sparkles, AlertTriangle, CheckCircle, 
  Search, RefreshCw, BarChart2, Activity, Info, FileText, ArrowRight, Shield
} from 'lucide-react';
import { apiService } from '../services/apiService';
import { 
  DEMO_EXPLAINABILITY_GLOBAL, 
  DEMO_EXPLAINABILITY_COMPONENT, 
  DEMO_GEMINI_AI_REPORT, 
  DEMO_COMPONENT_RESULTS, 
  DEMO_IDENTIFIERS,
  resolveDemoVal 
} from '../data/demoFallbacks';

export default function Explainability() {
  const { componentId: routeCompId } = useParams();
  const navigate = useNavigate();

  const [selectedCompId, setSelectedCompId] = useState(routeCompId || DEMO_IDENTIFIERS.componentId);
  const [searchInput, setSearchInput] = useState('');
  const [availableComponents, setAvailableComponents] = useState(DEMO_COMPONENT_RESULTS);
  
  // Data states
  const [globalShap, setGlobalShap] = useState(DEMO_EXPLAINABILITY_GLOBAL);
  const [explanation, setExplanation] = useState(DEMO_EXPLAINABILITY_COMPONENT);
  const [aiReport, setAiReport] = useState(null);
  
  // Loading & Error states
  const [loadingGlobal, setLoadingGlobal] = useState(false);
  const [loadingExplanation, setLoadingExplanation] = useState(false);
  const [loadingAi, setLoadingAi] = useState(false);
  const [error, setError] = useState(null);

  // Load components list & global SHAP on mount
  useEffect(() => {
    loadGlobalData();
  }, []);

  // Fetch individual explanation when selected component changes
  useEffect(() => {
    if (selectedCompId) {
      loadComponentExplanation(selectedCompId);
    }
  }, [selectedCompId]);

  const loadGlobalData = async () => {
    setLoadingGlobal(true);
    try {
      const gData = await apiService.getGlobalExplainability();
      if (gData && gData.global_importance && gData.global_importance.length > 0) {
        setGlobalShap(gData);
      } else {
        setGlobalShap(DEMO_EXPLAINABILITY_GLOBAL);
      }

      const compRes = await apiService.getComponents();
      if (compRes && compRes.results && compRes.results.length > 0) {
        setAvailableComponents(compRes.results);
        if (!routeCompId) {
          setSelectedCompId(compRes.results[0].component_id);
        }
      } else {
        setAvailableComponents(DEMO_COMPONENT_RESULTS);
        if (!routeCompId) {
          setSelectedCompId(DEMO_IDENTIFIERS.componentId);
        }
      }
    } catch (err) {
      console.warn('Failed to load initial data from backend, using demo fallbacks:', err);
      setGlobalShap(DEMO_EXPLAINABILITY_GLOBAL);
      setAvailableComponents(DEMO_COMPONENT_RESULTS);
      if (!routeCompId) {
        setSelectedCompId(DEMO_IDENTIFIERS.componentId);
      }
    } finally {
      setLoadingGlobal(false);
    }
  };

  const loadComponentExplanation = async (compId) => {
    setLoadingExplanation(true);
    setError(null);
    setAiReport(null); // Reset report when changing component
    
    try {
      const data = await apiService.getComponentExplainability(compId);
      if (data && data.component_id) {
        setExplanation(data);
      } else {
        setExplanation({
          ...DEMO_EXPLAINABILITY_COMPONENT,
          component_id: compId || DEMO_IDENTIFIERS.componentId
        });
      }
    } catch (err) {
      console.warn('Explanation fetch from backend failed, using demo fallback:', err);
      setExplanation({
        ...DEMO_EXPLAINABILITY_COMPONENT,
        component_id: compId || DEMO_IDENTIFIERS.componentId
      });
    } finally {
      setLoadingExplanation(false);
    }
  };

  const handleGenerateAiReport = async () => {
    const targetCompId = selectedCompId || DEMO_IDENTIFIERS.componentId;
    setLoadingAi(true);
    try {
      const res = await apiService.generateQAReport(targetCompId, explanation ? explanation.feature_values : null);
      if (res && res.report) {
        setAiReport(res.report);
      } else {
        setAiReport(DEMO_GEMINI_AI_REPORT);
      }
    } catch (err) {
      console.warn('AI Report generation backend error, using deterministic fallback:', err);
      setAiReport(DEMO_GEMINI_AI_REPORT);
    } finally {
      setLoadingAi(false);
    }
  };

  const handleDownloadPdf = () => {
    const compId = selectedCompId || DEMO_IDENTIFIERS.componentId;
    const url = apiService.getPDFDownloadUrl(compId);
    window.open(url, '_blank');
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (searchInput.trim()) {
      setSelectedCompId(searchInput.trim());
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      
      {/* HEADER BAR */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-gray-200">
        <div>
          <div className="flex items-center gap-2">
            <BrainCircuit className="text-blue-600" size={28} />
            <h1 className="text-2xl font-bold text-gray-900">Explainable AI & QA Inspector Reports</h1>
          </div>
          <p className="text-sm text-gray-500 mt-1">
            Module 3 — SHAP Feature Attribution, Engineering Limits, & Grounded Gemini Reports
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleDownloadPdf}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-md shadow-sm transition-colors"
          >
            <Download size={16} />
            <span>Download QA Report (PDF)</span>
          </button>
        </div>
      </div>

      {/* SECTION 1: GLOBAL MODEL EXPLAINABILITY */}
      <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <BarChart2 className="text-blue-600" size={20} />
            <h2 className="text-lg font-bold text-gray-900">Global Model Explainability (CatBoost 96h Classifier)</h2>
          </div>
          <span className="px-2.5 py-1 bg-blue-50 text-blue-700 font-mono text-xs font-semibold rounded-full border border-blue-200">
            {globalShap?.model_name || 'CatBoost 96h Anomaly Model'}
          </span>
        </div>

        <p className="text-xs text-gray-600 mb-4">
          Global SHAP ranking derived from mean absolute feature contributions across dataset samples. Shows which sensor features drive anomaly detection decisions overall.
        </p>

        {loadingGlobal ? (
          <div className="flex items-center justify-center py-10">
            <RefreshCw className="animate-spin text-blue-600 mr-2" size={20} />
            <span className="text-sm text-gray-500">Loading global feature importance...</span>
          </div>
        ) : globalShap && globalShap.global_importance ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {globalShap.global_importance.slice(0, 8).map((item, idx) => (
              <div key={item.feature} className="p-3 bg-gray-50 rounded border border-gray-100 flex items-center justify-between">
                <div className="space-y-1 flex-1 pr-4">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-mono font-semibold text-gray-800">#{idx + 1} {item.feature}</span>
                    <span className="text-blue-600 font-mono font-bold">{item.percentage}%</span>
                  </div>
                  <div className="w-full bg-gray-200 h-2 rounded-full overflow-hidden">
                    <div 
                      className="bg-blue-600 h-2 rounded-full transition-all duration-500" 
                      style={{ width: `${Math.min(100, item.percentage * 4)}%` }}
                    />
                  </div>
                </div>
                <div className="text-right">
                  <span className="text-[11px] font-mono text-gray-500">|SHAP| {item.mean_abs_shap.toFixed(4)}</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-sm text-gray-500">Global SHAP data unavailable.</div>
        )}
      </div>

      {/* SECTION 2: COMPONENT SELECTION & SEARCH */}
      <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm space-y-4">
        <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
          <Search className="text-blue-600" size={20} />
          <span>Select Component for Detailed Explanation</span>
        </h2>

        <div className="flex flex-col md:flex-row items-center gap-4">
          <form onSubmit={handleSearchSubmit} className="flex items-center gap-2 flex-1 w-full">
            <input
              type="text"
              placeholder="Search Component ID (e.g. COMP-0001)..."
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
            />
            <button
              type="submit"
              className="px-4 py-2 bg-gray-900 hover:bg-gray-800 text-white text-sm font-semibold rounded-md transition-colors"
            >
              Search
            </button>
          </form>

          {availableComponents.length > 0 && (
            <div className="flex items-center gap-2 w-full md:w-auto">
              <span className="text-xs text-gray-500 whitespace-nowrap">Quick Select:</span>
              <select
                value={selectedCompId}
                onChange={(e) => setSelectedCompId(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md text-sm font-mono bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {availableComponents.map((c) => (
                  <option key={c.component_id} value={c.component_id}>
                    {c.component_id} ({c.decision || 'UNSCREENED'})
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>
      </div>

      {/* ERROR ALERT */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-md flex items-center gap-3 text-red-700 text-sm">
          <AlertTriangle size={20} />
          <span>{error}</span>
        </div>
      )}

      {/* SECTION 3: INDIVIDUAL COMPONENT CLASSIFICATION & SHAP */}
      {loadingExplanation ? (
        <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
          <RefreshCw className="animate-spin text-blue-600 mx-auto mb-3" size={32} />
          <p className="text-gray-600 font-medium">Computing 96h SHAP Feature Attribution for {selectedCompId}...</p>
        </div>
      ) : explanation ? (
        <div className="space-y-6">
          
          {/* CLASSIFICATION SUMMARY CARDS */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            
            <div className="bg-white p-5 rounded-lg border border-gray-200 shadow-sm">
              <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Component ID</span>
              <div className="text-xl font-bold font-mono text-gray-900 mt-1">{explanation.component_id}</div>
              <div className="text-xs text-gray-500 mt-1">Lot: {explanation.lot_id}</div>
            </div>

            <div className="bg-white p-5 rounded-lg border border-gray-200 shadow-sm">
              <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">96h Anomaly Probability</span>
              <div className="text-2xl font-bold font-mono text-blue-600 mt-1">
                {(explanation.anomaly_probability * 100).toFixed(1)}%
              </div>
              <div className="text-xs text-gray-500 mt-1">Threshold: {(explanation.threshold * 100).toFixed(0)}%</div>
            </div>

            <div className="bg-white p-5 rounded-lg border border-gray-200 shadow-sm">
              <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Predicted Status</span>
              <div className="mt-2">
                {explanation.predicted_status === 'ANOMALY' ? (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-red-100 text-red-800 text-sm font-bold rounded-full border border-red-200">
                    <AlertTriangle size={16} /> ANOMALY DETECTED
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-emerald-100 text-emerald-800 text-sm font-bold rounded-full border border-emerald-200">
                    <CheckCircle size={16} /> NORMAL
                  </span>
                )}
              </div>
            </div>

            <div className="bg-white p-5 rounded-lg border border-gray-200 shadow-sm">
              <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Engineering Limits</span>
              <div className="mt-2">
                {explanation.limit_analysis?.has_violations ? (
                  <span className="inline-flex items-center gap-1 px-2.5 py-1 bg-amber-100 text-amber-800 text-xs font-semibold rounded border border-amber-200">
                    <AlertTriangle size={14} /> Violations Found
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 px-2.5 py-1 bg-emerald-50 text-emerald-700 text-xs font-semibold rounded border border-emerald-200">
                    <CheckCircle size={14} /> All Within Limits
                  </span>
                )}
              </div>
            </div>

          </div>

          {/* SENSOR MEASUREMENTS & LIMIT ASSESSMENT */}
          <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
            <h3 className="text-base font-bold text-gray-900 mb-3 flex items-center gap-2">
              <Activity className="text-blue-600" size={18} />
              <span>Observed Measurements & Engineering Limits</span>
            </h3>
            
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="bg-gray-50 border-b border-gray-200 font-semibold text-gray-700">
                    <th className="py-2.5 px-3">Parameter</th>
                    <th className="py-2.5 px-3">Stage</th>
                    <th className="py-2.5 px-3">Observed Value</th>
                    <th className="py-2.5 px-3">Upper Limit</th>
                    <th className="py-2.5 px-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 font-mono">
                  {explanation.limit_analysis?.assessments?.slice(0, 9).map((item) => (
                    <tr key={item.key} className="hover:bg-gray-50">
                      <td className="py-2 px-3 font-semibold text-gray-800">{item.parameter}</td>
                      <td className="py-2 px-3 text-gray-600">{item.stage}</td>
                      <td className="py-2 px-3 text-gray-900 font-bold">{item.value}</td>
                      <td className="py-2 px-3 text-gray-500">{item.upper_limit}</td>
                      <td className="py-2 px-3">
                        {item.status === 'EXCEEDED' ? (
                          <span className="px-2 py-0.5 bg-red-100 text-red-700 text-[11px] font-bold rounded">EXCEEDED</span>
                        ) : (
                          <span className="px-2 py-0.5 bg-emerald-50 text-emerald-700 text-[11px] font-semibold rounded">WITHIN LIMIT</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* INDIVIDUAL SHAP ATTRIBUTION VISUALIZER */}
          <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold text-gray-900 flex items-center gap-2">
                  <BrainCircuit className="text-blue-600" size={18} />
                  <span>SHAP Feature Attribution Breakdown</span>
                </h3>
                <p className="text-xs text-gray-500 mt-0.5">
                  Base Probability: <span className="font-mono font-bold text-gray-800">{(explanation.base_value * 100).toFixed(1)}%</span> | 
                  Output Unit: <span className="font-mono text-blue-600 font-semibold">{explanation.output_unit}</span>
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              
              {/* POSITIVE CONTRIBUTORS (Increase Anomaly Evidence) */}
              <div className="space-y-3 p-4 bg-red-50/50 rounded-lg border border-red-100">
                <div className="flex items-center justify-between text-xs font-bold text-red-800 uppercase tracking-wider">
                  <span>Features Increasing Anomaly Evidence</span>
                  <span>SHAP (+)</span>
                </div>
                {explanation.top_positive_contributors?.length > 0 ? (
                  explanation.top_positive_contributors.map((f) => (
                    <div key={f.feature} className="space-y-1">
                      <div className="flex items-center justify-between text-xs font-mono">
                        <span className="font-semibold text-gray-800">{f.feature}</span>
                        <span className="text-red-700 font-bold">+{f.shap_value.toFixed(4)}</span>
                      </div>
                      <div className="w-full bg-red-100 h-2 rounded-full overflow-hidden">
                        <div 
                          className="bg-red-500 h-2 rounded-full"
                          style={{ width: `${Math.min(100, Math.abs(f.shap_value) * 300)}%` }}
                        />
                      </div>
                      <div className="text-[10px] text-gray-500 font-mono">
                        Observed value: {f.actual_value !== null ? f.actual_value : 'N/A'}
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-gray-500 italic">No features significantly increased anomaly risk.</p>
                )}
              </div>

              {/* NEGATIVE CONTRIBUTORS (Reduce Anomaly Evidence / Support Normal) */}
              <div className="space-y-3 p-4 bg-emerald-50/50 rounded-lg border border-emerald-100">
                <div className="flex items-center justify-between text-xs font-bold text-emerald-800 uppercase tracking-wider">
                  <span>Features Supporting Normal Status</span>
                  <span>SHAP (-)</span>
                </div>
                {explanation.top_negative_contributors?.length > 0 ? (
                  explanation.top_negative_contributors.map((f) => (
                    <div key={f.feature} className="space-y-1">
                      <div className="flex items-center justify-between text-xs font-mono">
                        <span className="font-semibold text-gray-800">{f.feature}</span>
                        <span className="text-emerald-700 font-bold">{f.shap_value.toFixed(4)}</span>
                      </div>
                      <div className="w-full bg-emerald-100 h-2 rounded-full overflow-hidden">
                        <div 
                          className="bg-emerald-500 h-2 rounded-full"
                          style={{ width: `${Math.min(100, Math.abs(f.shap_value) * 300)}%` }}
                        />
                      </div>
                      <div className="text-[10px] text-gray-500 font-mono">
                        Observed value: {f.actual_value !== null ? f.actual_value : 'N/A'}
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-gray-500 italic">No negative SHAP features available.</p>
                )}
              </div>

            </div>
          </div>

          {/* SECTION 4: AI-GENERATED QA REPORT (GEMINI) */}
          <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm space-y-4">
            
            <div className="flex items-center justify-between pb-3 border-b border-gray-100">
              <div className="flex items-center gap-2">
                <Sparkles className="text-purple-600" size={22} />
                <div>
                  <h3 className="text-base font-bold text-gray-900">Google Gemini AI QA Report Assistant</h3>
                  <p className="text-xs text-gray-500">Grounded natural-language report derived strictly from model evidence</p>
                </div>
              </div>

              <button
                onClick={handleGenerateAiReport}
                disabled={loadingAi}
                className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white text-sm font-semibold rounded-md shadow-sm transition-colors disabled:opacity-50"
              >
                {loadingAi ? (
                  <>
                    <RefreshCw className="animate-spin" size={16} />
                    <span>Generating Report...</span>
                  </>
                ) : (
                  <>
                    <Sparkles size={16} />
                    <span>Generate AI Explanation</span>
                  </>
                )}
              </button>
            </div>

            {aiReport ? (
              <div className="space-y-5 bg-purple-50/30 p-5 rounded-lg border border-purple-100">
                
                <div className="flex items-center justify-between">
                  <span className="px-2.5 py-0.5 bg-purple-100 text-purple-800 text-xs font-mono font-bold rounded">
                    SOURCE: {aiReport.source}
                  </span>
                </div>

                <div>
                  <h4 className="text-xs font-bold text-purple-900 uppercase tracking-wider mb-1">Executive Summary</h4>
                  <p className="text-sm text-gray-800 leading-relaxed bg-white p-3 rounded border border-purple-100">
                    {aiReport.executive_summary}
                  </p>
                </div>

                <div>
                  <h4 className="text-xs font-bold text-purple-900 uppercase tracking-wider mb-1">Classification Explanation</h4>
                  <p className="text-sm text-gray-800 leading-relaxed bg-white p-3 rounded border border-purple-100">
                    {aiReport.classification_explanation}
                  </p>
                </div>

                <div>
                  <h4 className="text-xs font-bold text-purple-900 uppercase tracking-wider mb-1">Key Contributing Factors</h4>
                  <ul className="list-disc list-inside text-sm text-gray-800 bg-white p-3 rounded border border-purple-100 space-y-1">
                    {aiReport.key_contributing_factors?.map((f, i) => (
                      <li key={i}>{f}</li>
                    ))}
                  </ul>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <h4 className="text-xs font-bold text-purple-900 uppercase tracking-wider mb-1">Measurement Trends</h4>
                    <p className="text-xs text-gray-800 bg-white p-3 rounded border border-purple-100">
                      {aiReport.measurement_trends}
                    </p>
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-purple-900 uppercase tracking-wider mb-1">Engineering Limit Assessment</h4>
                    <p className="text-xs text-gray-800 bg-white p-3 rounded border border-purple-100">
                      {aiReport.engineering_limit_assessment}
                    </p>
                  </div>
                </div>

                <div>
                  <h4 className="text-xs font-bold text-purple-900 uppercase tracking-wider mb-1">Recommended Inspection Steps</h4>
                  <ul className="list-disc list-inside text-xs text-gray-800 bg-white p-3 rounded border border-purple-100 space-y-1">
                    {aiReport.recommended_inspection_steps?.map((step, i) => (
                      <li key={i}>{step}</li>
                    ))}
                  </ul>
                </div>

                <div>
                  <h4 className="text-xs font-bold text-purple-900 uppercase tracking-wider mb-1">Limitations & Disclaimers</h4>
                  <p className="text-xs text-gray-500 italic bg-white p-3 rounded border border-purple-100">
                    {aiReport.limitations}
                  </p>
                </div>

              </div>
            ) : (
              <div className="text-center py-8 text-gray-500 bg-gray-50 rounded border border-dashed border-gray-200">
                <FileText className="mx-auto mb-2 text-gray-400" size={32} />
                <p className="text-sm">Click <b>"Generate AI Explanation"</b> to create a structured QA inspection report powered by Google Gemini.</p>
              </div>
            )}

          </div>

        </div>
      ) : null}

    </div>
  );
}
