import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, Download, ShieldAlert, AlertTriangle, 
  Settings, CheckCircle2, List, Activity, Box, Cpu, Info, ArrowRight, ArrowDown, TrendingUp, Sparkles
} from 'lucide-react';
import { riskFusionService } from '../services/riskFusionService';
import { apiService } from '../services/apiService';
import { DEMO_IDENTIFIERS, DEMO_COMPONENT_DETAIL, resolveDemoVal } from '../data/demoFallbacks';

export default function RiskFusion() {
  const { componentId } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const response = await riskFusionService.getRiskFusion(componentId || 'CMP_00173');
        setData(response);
      } catch (error) {
        console.error("Failed to fetch risk fusion data", error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [componentId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#f8fafc] p-8 flex items-center justify-center font-sans">
        <div className="text-slate-400 font-bold tracking-widest text-sm flex items-center gap-2">
          <Activity className="w-4 h-4 animate-pulse" /> LOADING RISK FUSION...
        </div>
      </div>
    );
  }

  const rawData = data || DEMO_COMPONENT_DETAIL;
  const renderVal = (val, fallback = 'N/A') => {
    const res = resolveDemoVal(val, fallback);
    return res !== null && res !== undefined ? res : 'N/A';
  };
  
  // Extract values carefully with demo fallbacks
  const currentCompId = resolveDemoVal(rawData.component_id, componentId || DEMO_IDENTIFIERS.componentId);
  const currentLot = resolveDemoVal(rawData.lot, DEMO_IDENTIFIERS.lot);
  const currentDeviceType = resolveDemoVal(rawData.device_type, DEMO_IDENTIFIERS.deviceType);
  const currentStation = resolveDemoVal(rawData.station, DEMO_IDENTIFIERS.station);

  const aScore = resolveDemoVal(rawData.a_score, DEMO_COMPONENT_DETAIL.a_score);
  const sScore = resolveDemoVal(rawData.s_score, DEMO_COMPONENT_DETAIL.s_score);
  const predRisk = resolveDemoVal(rawData.prediction_risk, DEMO_COMPONENT_DETAIL.prediction_risk);
  const uncertRisk = resolveDemoVal(rawData.uncertainty_risk, DEMO_COMPONENT_DETAIL.uncertainty_risk);

  const pat = resolveDemoVal(rawData.evidence?.pat?.score, DEMO_COMPONENT_DETAIL.evidence.pat.score);
  const peer = resolveDemoVal(rawData.evidence?.peer_residual?.score, DEMO_COMPONENT_DETAIL.evidence.peer_residual.score);
  const temporal = resolveDemoVal(rawData.evidence?.early_temporal?.score, DEMO_COMPONENT_DETAIL.evidence.early_temporal.score);
  const isolation = resolveDemoVal(rawData.evidence?.isolation_forest?.score, DEMO_COMPONENT_DETAIL.evidence.isolation_forest.score);
  
  const leakagePrediction = resolveDemoVal(rawData.predicted_168h?.leakage, DEMO_COMPONENT_DETAIL.predicted_168h.leakage);
  const engUpper = resolveDemoVal(rawData.safety?.details?.Leakage_nA?.engineering_limit_upper, DEMO_COMPONENT_DETAIL.safety.details.Leakage_nA.engineering_limit_upper);
  
  let interval = 'N/A';
  if (rawData.predicted_168h?.interval && rawData.predicted_168h.interval.length === 2) {
    interval = `${rawData.predicted_168h.interval[0]} — ${rawData.predicted_168h.interval[1]}`;
  } else if (DEMO_COMPONENT_DETAIL.predicted_168h?.interval) {
    interval = `${DEMO_COMPONENT_DETAIL.predicted_168h.interval[0]} — ${DEMO_COMPONENT_DETAIL.predicted_168h.interval[1]}`;
  }
    
  const reasons = [];
  if (rawData.explanation && rawData.explanation !== 'N/A') reasons.push(rawData.explanation);
  if (rawData.warnings && rawData.warnings.length > 0) {
    rawData.warnings.forEach(w => { if (w && w !== 'N/A' && !reasons.includes(w)) reasons.push(w); });
  }
  if (reasons.length === 0) {
    reasons.push(...DEMO_COMPONENT_DETAIL.warnings);
  }

  const bModel = resolveDemoVal(rawData.basis?.b_model, DEMO_COMPONENT_DETAIL.basis.b_model);
  const qaDecision = resolveDemoVal(rawData.decision, DEMO_COMPONENT_DETAIL.decision);
  const ldi = resolveDemoVal(rawData.ldi, DEMO_COMPONENT_DETAIL.ldi);
  const fusionScore = resolveDemoVal(rawData.evidence?.fusion_state?.fusion_score ?? rawData.fusion_score, DEMO_COMPONENT_DETAIL.fusion_score);
  const testQuality = resolveDemoVal(rawData.test_integrity?.quality, "VALID");
  const testWithin = resolveDemoVal(rawData.test_integrity?.within_station, "PASS");
  const testCross = resolveDemoVal(rawData.test_integrity?.cross_station, "PASS");
  const testGlitch = resolveDemoVal(rawData.test_integrity?.glitch, "NONE");
  const decisionExplanation = resolveDemoVal(rawData.evidence?.explanation || rawData.explanation, DEMO_COMPONENT_DETAIL.explanation);

  return (
    <div className="min-h-screen bg-[#f8fafc] p-8 font-sans text-slate-800">
      
      {/* HEADER */}
      <div className="mb-6 border-b border-slate-200 pb-6">
        <div className="flex justify-between items-end">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 flex items-center">
              RISK FUSION & QA DECISION <span className="text-slate-400 font-normal mx-2">/</span> <span className="text-[#2563eb]">{currentCompId}</span>
            </h1>
            <div className="text-xs font-bold text-slate-500 tracking-widest uppercase mt-2 flex items-center gap-4">
              <span>{renderVal(currentLot)}</span>
              <span>{renderVal(currentDeviceType)}</span>
              <span>{renderVal(currentStation)}</span>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button 
              className="bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 text-xs font-bold uppercase tracking-wider px-4 py-2 rounded flex items-center gap-2 transition-colors"
              onClick={() => navigate(`/components/${currentCompId}/prediction`)}
            >
              <ArrowLeft className="w-4 h-4" /> Back to Prediction
            </button>
            <button 
              onClick={() => navigate(`/components/${currentCompId}/explainability`)}
              className="bg-purple-50 border border-purple-200 text-purple-700 hover:bg-purple-100 text-xs font-bold uppercase tracking-wider px-4 py-2 rounded flex items-center gap-2 transition-colors"
            >
              <Sparkles className="w-4 h-4 text-purple-600" /> AI Explainability & Report
            </button>
            <button 
              onClick={() => {
                const url = apiService.getPDFDownloadUrl(currentCompId);
                window.open(url, '_blank');
              }}
              className="bg-[#2563eb] hover:bg-[#1d4ed8] text-white text-xs font-bold uppercase tracking-wider px-4 py-2 rounded flex items-center gap-2 shadow-sm transition-colors"
            >
              <Download className="w-4 h-4" /> Download QA Report (PDF)
            </button>
          </div>
        </div>
      </div>

      {/* CURRENT STATE vs FUTURE STATE */}
      <div className="grid grid-cols-12 gap-6 mb-6">
        <div className="col-span-5 bg-white border border-slate-200 rounded shadow-sm p-6 flex flex-col justify-center text-center">
          <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Module A</div>
          <div className="text-sm font-bold text-slate-800 uppercase tracking-widest mb-4">CURRENT STATE</div>
          <div className="bg-slate-50 border border-slate-200 rounded p-6 mb-4">
            <div className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-2">A_SCORE</div>
            <div className="text-5xl font-light text-[#e11d48] tracking-tight">{renderVal(aScore)}</div>
          </div>
          <div className="text-xs text-slate-500 font-medium">Current-state anomaly evidence.</div>
        </div>

        <div className="col-span-2 flex items-center justify-center">
          <div className="flex flex-col items-center">
            <div className="h-0.5 w-16 bg-slate-200"></div>
            <ArrowRight className="w-6 h-6 text-slate-300 my-2" />
            <div className="h-0.5 w-16 bg-slate-200"></div>
          </div>
        </div>

        <div className="col-span-5 bg-white border border-slate-200 rounded shadow-sm p-6 flex flex-col justify-center text-center">
          <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Module B</div>
          <div className="text-sm font-bold text-slate-800 uppercase tracking-widest mb-4">FUTURE STATE</div>
          <div className="grid grid-cols-3 gap-3 mb-4">
             <div className="bg-slate-50 border border-slate-200 rounded p-4 text-center">
               <div className="text-[9px] font-bold text-slate-500 uppercase tracking-widest mb-2">S_SCORE</div>
               <div className="text-2xl font-medium text-slate-800">{renderVal(sScore)}</div>
             </div>
             <div className="bg-slate-50 border border-slate-200 rounded p-4 text-center">
               <div className="text-[9px] font-bold text-slate-500 uppercase tracking-widest mb-2 break-words">Pred. Risk</div>
               <div className="text-2xl font-medium text-slate-800">{renderVal(predRisk)}</div>
             </div>
             <div className="bg-slate-50 border border-slate-200 rounded p-4 text-center">
               <div className="text-[9px] font-bold text-slate-500 uppercase tracking-widest mb-2 break-words">Uncert. Risk</div>
               <div className="text-2xl font-medium text-slate-800">{renderVal(uncertRisk)}</div>
             </div>
          </div>
          <div className="text-xs text-slate-500 font-medium">Predicted future-state evidence.</div>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6 mb-6">
        {/* MODULE A EVIDENCE */}
        <div className="bg-white border border-slate-200 rounded shadow-sm p-6 flex flex-col">
          <div className="text-xs font-bold text-slate-500 tracking-widest uppercase mb-6 border-b border-slate-100 pb-3 flex items-center gap-2">
            <Activity className="w-4 h-4" /> CURRENT-STATE EVIDENCE
          </div>
          <div className="space-y-4 flex-1">
            <div className="flex justify-between items-center border-b border-slate-50 pb-2">
              <span className="text-xs font-semibold text-slate-500">PAT</span>
              <span className="text-sm font-bold text-slate-800">{renderVal(pat)}</span>
            </div>
            <div className="flex justify-between items-center border-b border-slate-50 pb-2">
              <span className="text-xs font-semibold text-slate-500">Peer Residual</span>
              <span className="text-sm font-bold text-slate-800">{renderVal(peer)}</span>
            </div>
            <div className="flex justify-between items-center border-b border-slate-50 pb-2">
              <span className="text-xs font-semibold text-slate-500">Early Temporal</span>
              <span className="text-sm font-bold text-[#e11d48]">{renderVal(temporal)}</span>
            </div>
            <div className="flex justify-between items-center border-b border-slate-50 pb-2">
              <span className="text-xs font-semibold text-slate-500">Isolation Forest</span>
              <span className="text-sm font-bold text-slate-800">{renderVal(isolation)}</span>
            </div>
          </div>
          <div className="mt-4 pt-4 border-t border-slate-200 flex justify-between items-center">
            <span className="text-xs font-bold text-slate-800 uppercase tracking-widest">A_SCORE</span>
            <span className="text-2xl font-bold text-[#e11d48]">{renderVal(aScore)}</span>
          </div>
        </div>

        {/* MODULE B EVIDENCE */}
        <div className="bg-white border border-slate-200 rounded shadow-sm p-6 flex flex-col">
          <div className="text-xs font-bold text-slate-500 tracking-widest uppercase mb-6 border-b border-slate-100 pb-3 flex items-center gap-2">
            <TrendingUp className="w-4 h-4" /> FUTURE-STATE EVIDENCE
          </div>
          <div className="space-y-4 flex-1">
            <div className="flex justify-between items-center border-b border-slate-50 pb-2">
              <span className="text-xs font-semibold text-slate-500">168h Leakage Prediction</span>
              <span className="text-sm font-bold text-[#2563eb]">{renderVal(leakagePrediction)} {leakagePrediction && 'nA'}</span>
            </div>
            <div className="flex justify-between items-center border-b border-slate-50 pb-2">
              <span className="text-xs font-semibold text-slate-500">Engineering Upper Limit</span>
              <span className="text-sm font-bold text-slate-400">{renderVal(engUpper)} {engUpper && 'nA'}</span>
            </div>
            <div className="flex justify-between items-center border-b border-slate-50 pb-2">
              <span className="text-xs font-semibold text-slate-500">Prediction Interval</span>
              <span className="text-sm font-bold text-slate-800">{interval} {interval !== 'N/A' && 'nA'}</span>
            </div>
            <div className="flex justify-between items-center border-b border-slate-50 pb-2">
              <span className="text-xs font-semibold text-slate-500">Prediction Risk</span>
              <span className="text-sm font-bold text-slate-800">{renderVal(predRisk)}</span>
            </div>
            <div className="flex justify-between items-center border-b border-slate-50 pb-2">
              <span className="text-xs font-semibold text-slate-500">Uncertainty Risk</span>
              <span className="text-sm font-bold text-slate-800">{renderVal(uncertRisk)}</span>
            </div>
          </div>
          <div className="mt-4 pt-4 border-t border-slate-200 flex justify-between items-center">
             <span className="text-xs font-bold text-slate-800 uppercase tracking-widest flex flex-col">
               S_SCORE <span className="text-[9px] text-slate-400 font-normal">Model: {bModel}</span>
             </span>
            <span className="text-2xl font-bold text-slate-700">{renderVal(sScore)}</span>
          </div>
        </div>

        {/* TEST INTEGRITY */}
        <div className="bg-white border border-slate-200 rounded shadow-sm p-6 flex flex-col">
          <div className="text-xs font-bold text-slate-500 tracking-widest uppercase mb-6 border-b border-slate-100 pb-3 flex items-center gap-2">
            <ShieldAlert className="w-4 h-4" /> TEST INTEGRITY
          </div>
          <div className="space-y-4 flex-1">
            <div className="flex justify-between items-center border-b border-slate-50 pb-2">
              <span className="text-xs font-semibold text-slate-500">Measurement Quality</span>
              <span className="text-[10px] font-bold bg-slate-50 text-slate-600 border border-slate-200 px-2 py-0.5 rounded uppercase tracking-wider">{renderVal(testQuality)}</span>
            </div>
            <div className="flex justify-between items-center border-b border-slate-50 pb-2">
              <span className="text-xs font-semibold text-slate-500">Within-Station</span>
              <span className="text-[10px] font-bold bg-slate-50 text-slate-600 border border-slate-200 px-2 py-0.5 rounded uppercase tracking-wider">{renderVal(testWithin)}</span>
            </div>
            <div className="flex justify-between items-center border-b border-slate-50 pb-2">
              <span className="text-xs font-semibold text-slate-500">Cross-Station</span>
              <span className="text-[10px] font-bold bg-slate-50 text-slate-600 border border-slate-200 px-2 py-0.5 rounded uppercase tracking-wider">{renderVal(testCross)}</span>
            </div>
            <div className="flex justify-between items-center border-b border-slate-50 pb-2">
              <span className="text-xs font-semibold text-slate-500">Glitch Detection</span>
              <span className="text-[10px] font-bold bg-slate-50 text-slate-600 border border-slate-200 px-2 py-0.5 rounded uppercase tracking-wider">{renderVal(testGlitch)}</span>
            </div>
          </div>
          <div className="mt-4 pt-4 border-t border-slate-200 flex justify-between items-center">
            <span className="text-xs font-bold text-slate-800 uppercase tracking-widest">STATION</span>
            <span className="text-sm font-mono font-bold text-slate-600">{renderVal(currentStation)}</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-12 gap-6 mb-6">
        {/* RISK EVIDENCE FLOW */}
        <div className="col-span-8 bg-[#0f172a] border border-slate-800 rounded shadow-sm p-8 text-white relative overflow-hidden">
          <div className="text-xs font-bold text-slate-400 tracking-widest uppercase mb-8 text-center relative z-10">RISK EVIDENCE FLOW ARCHITECTURE</div>
          
          <div className="flex flex-col items-center max-w-2xl mx-auto relative z-10">
            {/* Top Row: Current State */}
            <div className="flex w-full justify-center">
              <div className="bg-slate-800 border border-slate-600 px-4 py-2 rounded text-xs font-bold uppercase tracking-widest text-slate-300">
                CURRENT-STATE EVIDENCE
              </div>
            </div>
            <ArrowDown className="w-5 h-5 text-slate-500 my-2" />
            <div className="bg-[#e11d48]/20 border border-[#e11d48]/50 text-[#fca5a5] px-6 py-2 rounded font-bold text-sm">
              A_SCORE
            </div>
            
            <div className="h-6 w-px bg-slate-600 my-2"></div>
            
            {/* Split Row: Future & Test Integrity */}
            <div className="flex w-full justify-between items-start border-t border-slate-600 pt-6 mt-2 relative">
              <div className="absolute top-0 left-1/4 right-1/4 h-px bg-slate-600"></div>
              
              <div className="flex flex-col items-center flex-1">
                <ArrowDown className="w-5 h-5 text-slate-500 mb-2" />
                <div className="bg-slate-800 border border-slate-600 px-4 py-2 rounded text-xs font-bold uppercase tracking-widest text-slate-300 mb-2">
                  FUTURE-STATE EVIDENCE
                </div>
                <ArrowDown className="w-4 h-4 text-slate-500 mb-2" />
                <div className="bg-[#2563eb]/20 border border-[#2563eb]/50 text-[#93c5fd] px-6 py-2 rounded font-bold text-sm mb-2">
                  S_SCORE
                </div>
                <ArrowDown className="w-4 h-4 text-slate-500 mb-2" />
                <div className="bg-slate-700 border border-slate-500 text-slate-200 px-4 py-1.5 rounded text-xs font-bold mb-2">
                  PREDICTION RISK
                </div>
                <ArrowDown className="w-4 h-4 text-slate-500 mb-2" />
                <div className="bg-slate-700 border border-slate-500 text-slate-200 px-4 py-1.5 rounded text-xs font-bold">
                  UNCERTAINTY RISK
                </div>
              </div>

              <div className="flex flex-col items-center flex-1">
                <ArrowDown className="w-5 h-5 text-slate-500 mb-2" />
                <div className="bg-slate-800 border border-slate-600 px-4 py-2 rounded text-xs font-bold uppercase tracking-widest text-slate-300">
                  TEST INTEGRITY
                </div>
              </div>
            </div>

            <div className="flex w-full justify-center relative mt-6 pt-6">
              <div className="absolute top-0 left-1/4 right-1/4 h-px border-b border-dashed border-slate-500"></div>
              <div className="absolute top-0 left-1/2 w-px h-6 border-r border-dashed border-slate-500"></div>
              
              <div className="flex flex-col items-center mt-2">
                <ArrowDown className="w-5 h-5 text-slate-400 mb-2" />
                <div className="bg-amber-500/20 border border-amber-500/50 text-amber-200 px-8 py-3 rounded-lg font-bold text-base tracking-widest uppercase mb-3 shadow-[0_0_15px_rgba(245,158,11,0.2)]">
                  RISK FUSION
                </div>
                <ArrowDown className="w-6 h-6 text-amber-500 mb-2" />
                <div className="bg-white text-slate-900 px-10 py-3 rounded-lg font-black text-lg tracking-widest uppercase shadow-[0_0_20px_rgba(255,255,255,0.2)]">
                  QA DECISION
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* DECISION BASIS & WHY FLAGGED */}
        <div className="col-span-4 flex flex-col gap-6">
          <div className="bg-white border border-slate-200 rounded shadow-sm p-6 flex-1 flex flex-col">
            <div className="text-xs font-bold text-slate-500 tracking-widest uppercase mb-5 border-b border-slate-100 pb-3 flex items-center gap-2">
              <List className="w-4 h-4" /> DECISION BASIS
            </div>
            <div className="space-y-3 flex-1 text-sm">
              <div className="grid grid-cols-2 gap-2 pb-2 border-b border-slate-50">
                <span className="text-slate-500 font-semibold">LDI (Latent Defect Index):</span>
                <span className="font-bold text-slate-800">{renderVal(ldi)}</span>
              </div>
              <div className="grid grid-cols-2 gap-2 pb-2 border-b border-slate-50">
                <span className="text-slate-500 font-semibold">Fusion Score:</span>
                <span className="font-bold text-slate-800">{renderVal(fusionScore)}</span>
              </div>
              <div className="grid grid-cols-2 gap-2 pb-2 border-b border-slate-50">
                <span className="text-slate-500 font-semibold">Test Integrity:</span>
                <span className="font-bold text-emerald-600">{renderVal(testQuality)}</span>
              </div>
              <div className="grid grid-cols-2 gap-2 pb-2 border-b border-slate-50">
                <span className="text-slate-500 font-semibold">Prediction:</span>
                <span className="font-bold text-amber-600">{renderVal(leakagePrediction)} {leakagePrediction && 'nA'}</span>
              </div>
            </div>
          </div>

          <div className="bg-white border border-slate-200 rounded shadow-sm p-6 flex-1 flex flex-col">
            <div className="text-xs font-bold text-slate-500 tracking-widest uppercase mb-5 border-b border-slate-100 pb-3 flex items-center gap-2">
              <Info className="w-4 h-4" /> DECISION EXPLANATION
            </div>
            <div className="text-sm font-semibold text-slate-600">
              {decisionExplanation}
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-12 gap-6 mb-6">
        {/* WHY WAS THIS FLAGGED */}
        <div className="col-span-8 bg-white border border-slate-200 rounded shadow-sm p-6">
          <div className="text-xs font-bold text-slate-500 tracking-widest uppercase mb-6 flex items-center gap-2">
            <ShieldAlert className="w-4 h-4" /> WHY THIS COMPONENT REQUIRES REVIEW
          </div>
          <div className="space-y-4">
            {reasons.map((reason, idx) => (
              <div key={idx} className="flex gap-4 items-start bg-slate-50 p-4 rounded border border-slate-100">
                <div className="flex-shrink-0 w-6 h-6 rounded bg-white border border-slate-200 flex items-center justify-center text-[10px] font-bold text-slate-500 shadow-sm">{idx + 1}</div>
                <div className="text-sm text-slate-700 font-medium leading-relaxed pt-0.5">{reason}</div>
              </div>
            ))}
          </div>
        </div>

        {/* FINAL QA DECISION CARD */}
        <div className="col-span-4 bg-[#fff1f2] border-2 border-[#fecdd3] rounded-xl shadow-sm p-8 text-center flex flex-col items-center justify-center relative overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-2 bg-[#e11d48]"></div>
          
          <div className="text-xs font-bold text-[#be123c] tracking-widest uppercase mb-2">FINAL QA DECISION</div>
          <div className="text-3xl font-black text-[#9f1239] uppercase tracking-tight mb-6">
            {typeof qaDecision === 'string' ? qaDecision.replace('_', ' ') : qaDecision}
          </div>
          
          <div className="w-full bg-white/60 border border-[#fecdd3] rounded p-4 mb-6 text-left">
            <div className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2 text-center">Decision Basis</div>
            <div className="text-xs font-bold text-slate-700 text-center flex flex-col gap-1">
              <span>{decisionExplanation}</span>
            </div>
          </div>

          <div className="flex flex-col gap-3 w-full">
            <button 
              onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
              className="bg-[#e11d48] hover:bg-[#be123c] text-white text-xs font-bold uppercase tracking-widest px-4 py-3 rounded flex items-center justify-center gap-2 transition-colors w-full"
            >
               View Full Evidence
            </button>
            <button 
              onClick={() => {
                const url = apiService.getPDFDownloadUrl(currentCompId);
                window.open(url, '_blank');
              }}
              className="bg-white border border-[#fecdd3] text-[#e11d48] hover:bg-[#ffe4e6] text-xs font-bold uppercase tracking-widest px-4 py-3 rounded flex items-center justify-center gap-2 transition-colors w-full"
            >
               <Download className="w-4 h-4" /> Export QA Report (PDF)
            </button>
          </div>
        </div>
      </div>

    </div>
  );
}
