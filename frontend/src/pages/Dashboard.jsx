import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload, Play, Loader2, Cpu, Database, CheckCircle2, XCircle, AlertTriangle, RefreshCw, ArrowRight, Eye, Download, FileText, FileSpreadsheet } from 'lucide-react';
import { apiService, API_BASE } from '../services/apiService';
import { DEMO_IDENTIFIERS, DEMO_DASHBOARD_SUMMARY, DEMO_COMPONENT_RESULTS } from '../data/demoFallbacks';

const SparklineSVG = ({ color, data }) => (
  <svg width="60" height="24" viewBox="0 0 60 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d={data} stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

export default function Dashboard() {
  const navigate = useNavigate();
  const fileInputRef = React.useRef(null);
  
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [fileUploaded, setFileUploaded] = useState(false);
  const [screeningRunning, setScreeningRunning] = useState(false);
  const [screeningProgress, setScreeningProgress] = useState('');
  const [screeningStatus, setScreeningStatus] = useState(null);
  const [screeningError, setScreeningError] = useState(null);

  const [summary, setSummary] = useState({
    pass: 0, monitor: 0, review: 0, reject: 0, repeat_measurement: 0, data_unavailable: 0
  });
  const [results, setResults] = useState([]);
  const [latestRunId, setLatestRunId] = useState(null);
  const [selectedLotId, setSelectedLotId] = useState(localStorage.getItem('selectedLotId') || DEMO_IDENTIFIERS.lot);
  const [exportingCsv, setExportingCsv] = useState(false);
  const [exportingPdf, setExportingPdf] = useState(false);
  const [exportError, setExportError] = useState(null);

  const loadDashboardData = async (lotId = null) => {
    try {
      const data = await apiService.getComponents(lotId);
      if (data && data.summary) {
        setSummary(data.summary);
        setResults(data.results || []);
        if (data.latest_run_id) setLatestRunId(data.latest_run_id);
      }
    } catch (err) {
      console.warn("Failed to load component history for lot:", lotId, err);
    }
  };

  useEffect(() => {
    const currentLot = localStorage.getItem('selectedLotId') || DEMO_IDENTIFIERS.lot;
    setSelectedLotId(currentLot);
    loadDashboardData(currentLot);

    const onLotChange = (e) => {
      const newLot = e.detail?.lotId;
      if (newLot) {
        setSelectedLotId(newLot);
        loadDashboardData(newLot);
      }
    };

    window.addEventListener('appLotChanged', onLotChange);
    return () => window.removeEventListener('appLotChanged', onLotChange);
  }, []);

  const handleUpload = async (e) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;
    
    setUploading(true);
    setFile(selectedFile);
    // Simulate short UI delay for upload feel
    setTimeout(() => {
      setUploading(false);
      setFileUploaded(true);
      setScreeningStatus(null);
      setScreeningError(null);
      setScreeningProgress('');
    }, 500);
  };

  const handleRunScreening = async () => {
    if (!fileUploaded || !file) {
      alert("Please upload a dataset first.");
      return;
    }
    
    setScreeningRunning(true);
    setScreeningStatus(null);
    setScreeningError(null);
    setScreeningProgress('Initiating batch pipeline...');
    
    try {
      const data = await apiService.batchScreen(file, (msg) => {
        setScreeningProgress(msg);
      });
      setSummary(data.summary);
      setResults(data.results || []);
      setScreeningStatus('passed');
      navigate('/anomaly');
    } catch (error) {
      console.error("Screening failed", error);
      setScreeningStatus('failed');
      setScreeningError(error.message || 'Unknown error occurred during screening.');
    } finally {
      setScreeningRunning(false);
      setScreeningProgress('');
    }
  };

  const handleExport = async (type) => {
    const runIdToExport = latestRunId || DEMO_IDENTIFIERS.runId;
    if (!runIdToExport) return;
    const setExporting = type === 'csv' ? setExportingCsv : setExportingPdf;
    setExporting(true);
    setExportError(null);
    try {
      const response = await fetch(`${API_BASE}/screening-runs/${runIdToExport}/export/${type}`).catch(() => null);
      if (response && response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `QA_Report_${runIdToExport}.${type}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        a.remove();
        return;
      }
      
      // If run not in DB yet (prototype mode), fallback generate CSV or component PDF
      if (type === 'csv') {
        const headers = ["component_id", "lot_id", "station", "a_score", "ldi", "stage", "decision"];
        const rows = (results.length > 0 ? results : DEMO_COMPONENT_RESULTS).map(r => [
          r.component_id, r.lot || DEMO_IDENTIFIERS.lot, r.station || DEMO_IDENTIFIERS.station, r.a_score, r.ldi, r.stage, r.decision
        ]);
        const csvContent = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `QA_Report_${runIdToExport}.csv`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        a.remove();
        return;
      } else {
        const compId = (results.length > 0 ? results[0].component_id : DEMO_IDENTIFIERS.componentId);
        const compPdfRes = await fetch(`${API_BASE}/api/reports/qa/${compId}/pdf`).catch(() => null);
        if (compPdfRes && compPdfRes.ok) {
          const blob = await compPdfRes.blob();
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `QA_Inspection_Report_${compId}.pdf`;
          document.body.appendChild(a);
          a.click();
          window.URL.revokeObjectURL(url);
          a.remove();
          return;
        }
      }
      throw new Error('Export service unavailable');
    } catch (err) {
      setExportError(`Failed to export ${type.toUpperCase()}`);
      console.error(err);
      setTimeout(() => setExportError(null), 3000);
    } finally {
      setExporting(false);
    }
  };

  const renderVal = (val) => val !== null && val !== undefined ? val : 'N/A';
  
  const rawTotal = Object.values(summary).reduce((acc, val) => acc + val, 0);
  const displaySummary = (rawTotal > 0 || results.length > 0) ? summary : DEMO_DASHBOARD_SUMMARY;
  const currentLotId = selectedLotId || ((results.length > 0 && results[0].lot) ? results[0].lot : DEMO_IDENTIFIERS.lot);
  const displayResults = results.length > 0 
    ? results 
    : DEMO_COMPONENT_RESULTS.map(c => ({ ...c, lot: currentLotId }));
  const displayLatestRunId = latestRunId || DEMO_IDENTIFIERS.runId;

  const totalUnits = Object.values(displaySummary).reduce((acc, val) => acc + val, 0);
  const pct = (val) => totalUnits > 0 ? ((val / totalUnits) * 100).toFixed(1) : '0.0';
  
  const anomalousUnits = displayResults.filter(r => 
    r.decision === 'REJECT' || r.decision === 'REVIEW_REQUIRED' || r.decision === 'REPEAT_MEASUREMENT'
  );

  return (
    <div className="min-h-screen bg-[#F8F9FA] bg-[radial-gradient(#E5E7EB_1px,transparent_1px)] [background-size:16px_16px] px-3 py-4 md:px-6 md:py-6 font-sans text-gray-900">
      <div className="max-w-[1440px] mx-auto">
        
        {/* HEADER */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-3">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-[#F0F2FF] text-[#4F46E5] rounded-xl flex items-center justify-center shadow-sm">
              <Cpu size={24} />
            </div>
            <div>
              <h1 className="text-[28px] font-bold tracking-tight text-[#111827] leading-tight">Burn-In Screening</h1>
              <p className="text-[#6B7280] text-[15px]">Accelerating reliability. Detecting issues early.</p>
            </div>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 bg-[#F3F4F6] px-3 py-1.5 rounded-lg border border-gray-200">
              <Database size={14} className="text-gray-500" />
              <span className="text-[13px] text-gray-600 font-medium">Lot <span className="text-[#4F46E5] bg-[#EEF2FF] px-1.5 py-0.5 rounded font-bold ml-1">{currentLotId}</span></span>
            </div>
            
            {displayLatestRunId && (
              <div className="flex items-center gap-2 border-r border-gray-200 pr-4">
                <span className="text-[12px] font-semibold text-gray-500">QA REPORT:</span>
                <button 
                  onClick={() => handleExport('csv')}
                  disabled={exportingCsv || exportingPdf}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-[13px] font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors disabled:opacity-50"
                >
                  {exportingCsv ? <Loader2 size={14} className="animate-spin" /> : <FileSpreadsheet size={14} className="text-[#10B981]" />}
                  CSV
                </button>
                <button 
                  onClick={() => handleExport('pdf')}
                  disabled={exportingCsv || exportingPdf}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-[13px] font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors disabled:opacity-50"
                >
                  {exportingPdf ? <Loader2 size={14} className="animate-spin" /> : <FileText size={14} className="text-[#EF4444]" />}
                  PDF
                </button>
              </div>
            )}

            <input type="file" ref={fileInputRef} className="hidden" onChange={handleUpload} />
            <button 
              className={`flex items-center gap-2 px-4 py-2 border rounded-lg text-sm font-semibold shadow-sm transition-colors ${fileUploaded ? 'bg-green-50 border-green-200 text-green-700 hover:bg-green-100' : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'}`}
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading}
            >
              {uploading ? <Loader2 size={16} className="animate-spin text-gray-500" /> : (fileUploaded ? <CheckCircle2 size={16} className="text-green-600" /> : <Upload size={16} className="text-gray-500" />)}
              {uploading ? 'Uploading...' : (fileUploaded ? 'Dataset Uploaded' : 'Upload Dataset')}
            </button>
            <button 
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold shadow-sm transition-colors ${!fileUploaded ? 'bg-gray-300 text-gray-500 cursor-not-allowed' : 'bg-[#3F51B5] hover:bg-[#3949AB] text-white shadow-[#3F51B5]/30'}`}
              onClick={handleRunScreening}
              disabled={!fileUploaded || screeningRunning}
            >
              {screeningRunning ? <Loader2 size={16} className="animate-spin" /> : <Play size={16} className="fill-current" />}
              {screeningRunning ? (screeningProgress || 'Running Screening...') : 'Run Screening'}
            </button>
          </div>
        </div>

        {/* SCREENING ERROR BANNER */}
        {screeningStatus === 'failed' && (
          <div className="bg-red-50 border border-red-200 p-4 rounded-xl mb-6 flex items-start gap-3 shadow-sm">
            <XCircle className="w-5 h-5 mt-0.5 text-red-500 shrink-0" />
            <div>
              <h3 className="font-bold text-[#991B1B] text-[15px]">Screening Failed</h3>
              <p className="text-[#B91C1C] text-[13px] mt-1 font-medium">
                The dataset encountered an error during the batch screening process.
              </p>
              <div className="mt-3 bg-white/60 border border-red-100 rounded p-3 text-[13px] text-[#7F1D1D] font-mono space-y-1.5">
                <div><span className="font-bold text-red-800">Details:</span> {screeningError || 'API Error'}</div>
              </div>
            </div>
          </div>
        )}

        {/* EXPORT ERROR BANNER */}
        {exportError && (
          <div className="bg-red-50 border border-red-200 p-3 rounded-xl mb-6 flex items-center justify-between shadow-sm">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-red-500" />
              <span className="text-red-800 font-medium text-sm">{exportError}</span>
            </div>
          </div>
        )}

        {/* KPI CARDS */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          {/* Static Pass */}
          <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100 flex items-center justify-between relative overflow-hidden">
            <div className="absolute left-0 top-0 bottom-0 w-[4px] bg-[#22C55E]"></div>
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 rounded-full bg-[#DCFCE7] text-[#16A34A] flex items-center justify-center shrink-0">
                <CheckCircle2 size={20} className="fill-current text-white bg-[#16A34A] rounded-full" />
              </div>
              <div>
                <div className="text-3xl font-bold text-gray-900 tracking-tight">{displaySummary.pass}</div>
                <div className="text-[13px] text-gray-500 font-medium mt-0.5">Static Pass</div>
              </div>
            </div>
            <div className="opacity-70 mt-[-20px] mr-2">
              <SparklineSVG color="#22C55E" data="M0 20 C10 20, 15 10, 25 15 C35 20, 45 5, 60 10" />
            </div>
          </div>

          {/* Reject */}
          <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100 flex items-center justify-between relative overflow-hidden">
            <div className="absolute left-0 top-0 bottom-0 w-[4px] bg-[#EF4444]"></div>
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 rounded-full bg-[#FEE2E2] text-[#DC2626] flex items-center justify-center shrink-0">
                <XCircle size={20} className="fill-current text-white bg-[#DC2626] rounded-full" />
              </div>
              <div>
                <div className="text-3xl font-bold text-gray-900 tracking-tight">{displaySummary.reject}</div>
                <div className="text-[13px] text-gray-500 font-medium mt-0.5">Reject</div>
              </div>
            </div>
            <div className="opacity-70 mt-[-20px] mr-2">
              <SparklineSVG color="#EF4444" data="M0 10 C10 10, 20 20, 30 15 C40 10, 50 5, 60 15" />
            </div>
          </div>

          {/* Anomalies */}
          <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100 flex items-center justify-between relative overflow-hidden">
            <div className="absolute left-0 top-0 bottom-0 w-[4px] bg-[#F59E0B]"></div>
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 rounded-full bg-[#FEF3C7] text-[#D97706] flex items-center justify-center shrink-0">
                <AlertTriangle size={20} className="fill-current text-[#D97706]" />
              </div>
              <div>
                <div className="text-3xl font-bold text-gray-900 tracking-tight">{displaySummary.review}</div>
                <div className="text-[13px] text-gray-500 font-medium mt-0.5">Anomalies</div>
              </div>
            </div>
            <div className="opacity-70 mt-[-20px] mr-2">
              <SparklineSVG color="#F59E0B" data="M0 20 C15 20, 25 15, 35 20 C45 25, 50 5, 60 10" />
            </div>
          </div>

          {/* Repeat */}
          <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100 flex items-center justify-between relative overflow-hidden">
            <div className="absolute left-0 top-0 bottom-0 w-[4px] bg-[#8B5CF6]"></div>
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 rounded-full bg-[#EDE9FE] text-[#7C3AED] flex items-center justify-center shrink-0">
                <RefreshCw size={20} />
              </div>
              <div>
                <div className="text-3xl font-bold text-gray-900 tracking-tight">{displaySummary.repeat_measurement}</div>
                <div className="text-[13px] text-gray-500 font-medium mt-0.5">Repeat</div>
              </div>
            </div>
            <div className="opacity-70 mt-[-20px] mr-2">
              <SparklineSVG color="#8B5CF6" data="M0 15 C10 10, 20 5, 30 15 C40 25, 50 10, 60 10" />
            </div>
          </div>
        </div>

        {/* DECISION DISTRIBUTION */}
        <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100 mb-6">
          <div className="flex justify-between items-end mb-4">
            <div>
              <h2 className="text-[19px] font-bold text-gray-900 mb-1">Decision Distribution</h2>
              <p className="text-[14px] text-gray-500">Breakdown of screening results for this lot.</p>
            </div>
            <div className="text-right">
              <div className="text-[12px] text-gray-500 font-medium mb-1">Total Units</div>
              <div className="text-2xl font-bold text-gray-900 leading-none">{totalUnits}</div>
            </div>
          </div>

          <div className="w-full">
            <div className="flex h-10 w-full rounded-lg overflow-hidden border border-gray-100 text-white text-[13px] font-bold">
              {displaySummary.pass > 0 && <div className="h-full bg-[#52C473] flex items-center justify-center" style={{ width: `${pct(displaySummary.pass)}%` }}>{pct(displaySummary.pass)}%</div>}
              {displaySummary.monitor > 0 && <div className="h-full bg-[#C2935B] flex items-center justify-center" style={{ width: `${pct(displaySummary.monitor)}%` }}>{pct(displaySummary.monitor)}%</div>}
              {displaySummary.review > 0 && <div className="h-full bg-[#F8A042] flex items-center justify-center" style={{ width: `${pct(displaySummary.review)}%` }}>{pct(displaySummary.review)}%</div>}
              {displaySummary.reject > 0 && <div className="h-full bg-[#DC5C64] flex items-center justify-center" style={{ width: `${pct(displaySummary.reject)}%` }}>{pct(displaySummary.reject)}%</div>}
              {displaySummary.repeat_measurement > 0 && <div className="h-full bg-[#9B6EE1] flex items-center justify-center" style={{ width: `${pct(displaySummary.repeat_measurement)}%` }}>{pct(displaySummary.repeat_measurement)}%</div>}
              {displaySummary.data_unavailable > 0 && <div className="h-full bg-gray-400 flex items-center justify-center" style={{ width: `${pct(displaySummary.data_unavailable)}%` }}>{pct(displaySummary.data_unavailable)}%</div>}
            </div>
            
            <div className="flex flex-wrap justify-center gap-6 text-[13px] mt-5 font-medium text-gray-600">
              <div className="flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-[#52C473]"></span> Pass ({displaySummary.pass})</div>
              <div className="flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-[#C2935B]"></span> Monitor ({displaySummary.monitor})</div>
              <div className="flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-[#F8A042]"></span> Review ({displaySummary.review})</div>
              <div className="flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-[#DC5C64]"></span> Reject ({displaySummary.reject})</div>
              <div className="flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-[#9B6EE1]"></span> Repeat ({displaySummary.repeat_measurement})</div>
            </div>
          </div>
        </div>

        {/* UNITS WITH ANOMALIES */}
        <div className="bg-[#FFFDF7] rounded-xl shadow-sm border border-[#FBE5C4] overflow-hidden">
          <div className="p-5 pb-3 flex justify-between items-start border-b border-[#FBE5C4]">
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 rounded-lg bg-[#FEF3C7] text-[#D97706] flex items-center justify-center mt-1">
                <AlertTriangle size={20} className="fill-current text-[#D97706]" />
              </div>
              <div>
                <h2 className="text-[19px] font-bold text-[#1F2937] mb-1">Units with Anomalies</h2>
                <p className="text-[14px] text-gray-600">These units require investigation or follow-up.</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-1.5 bg-[#FEF3C7] text-[#B45309] px-3 py-1.5 rounded-full text-[13px] font-bold">
                <AlertTriangle size={14} className="fill-current text-[#B45309]" /> Action Required
              </div>
              <div className="text-[18px] font-bold text-[#1F2937]">{anomalousUnits.length} units</div>
            </div>
          </div>

          <div className="w-full overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-[#FBE5C4] text-[13px] text-gray-500 font-semibold bg-white/50">
                  <th className="py-2 px-4 font-medium">Unit ID</th>
                  <th className="py-2 px-4 font-medium">Lot</th>
                  <th className="py-2 px-4 font-medium">A_Score</th>
                  <th className="py-2 px-4 font-medium">LDI</th>
                  <th className="py-2 px-4 font-medium">Stage</th>
                  <th className="py-2 px-4 font-medium">Decision</th>
                  <th className="py-2 px-4 font-medium">Action</th>
                </tr>
              </thead>
              <tbody>
                {anomalousUnits.slice(0, 5).map((comp, i) => (
                  <tr key={comp.component_id} className={`border-b border-gray-100 ${i % 2 === 0 ? 'bg-white' : 'bg-[#FAFAFA]'}`}>
                    <td className="py-2 px-4 text-[14px] text-gray-900 font-mono">{renderVal(comp.component_id)}</td>
                    <td className="py-2 px-4 text-[14px] text-gray-600">{renderVal(comp.lot)}</td>
                    <td className="py-2 px-4 text-[14px] text-[#e11d48] font-bold">{renderVal(comp.a_score)}</td>
                    <td className="py-2 px-4 text-[14px] text-gray-600">{renderVal(comp.ldi)}</td>
                    <td className="py-2 px-4 text-[14px] text-gray-600">{renderVal(comp.stage)}</td>
                    <td className="py-2 px-4 text-[14px] font-bold text-[#b91c1c] uppercase">{renderVal(comp.decision)}</td>
                    <td className="py-2 px-4">
                      <button 
                        className="bg-[#FEF3C7] hover:bg-[#FDE68A] text-[#B45309] px-4 py-1 rounded-full text-[13px] font-semibold transition-colors flex items-center gap-1"
                        onClick={() => navigate(`/components/${comp.component_id}/prediction`)}
                      >
                        <Eye size={12} /> Review
                      </button>
                    </td>
                  </tr>
                ))}
                {anomalousUnits.length === 0 && (
                  <tr>
                    <td colSpan="7" className="py-4 text-center text-gray-500 text-sm bg-white">No anomalies detected.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
          
          <div className="p-4 px-6 bg-white flex justify-between items-center text-[13px]">
            <div className="text-gray-500 font-medium">
              Showing {Math.min(anomalousUnits.length, 5)} of {anomalousUnits.length} units
            </div>
            <button 
              className="text-[#4F46E5] font-semibold flex items-center gap-1 hover:underline"
              onClick={() => navigate('/anomaly')}
            >
              View all anomalies <ArrowRight size={14} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
