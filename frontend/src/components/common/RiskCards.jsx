import React from 'react';
import { Shield, Activity, TrendingUp } from 'lucide-react';

export function RiskCard({ title, icon: Icon, value, status, description }) {
  const getStatusColor = () => {
    if (status === 'PASS' || status === 'NORMAL') return 'text-status-pass';
    if (status === 'MONITOR' || status === 'ELEVATED') return 'text-status-monitor';
    if (status === 'REVIEW' || status === 'HIGH') return 'text-status-review';
    if (status === 'REJECT' || status === 'DETECTED') return 'text-status-reject';
    return 'text-text-muted';
  };

  return (
    <div className="card flex flex-col justify-between">
      <div className="border-b border-border-subtle pb-3 mb-3">
        <div className="flex items-center gap-2">
          <Icon size={14} className="text-[#6B7A8C]" strokeWidth={2.5} />
          <span className="text-[10px] font-bold text-[#6B7A8C] tracking-[0.06em] uppercase">{title}</span>
        </div>
      </div>
      
      <div className="flex flex-col justify-end">
        <div className={`font-mono text-3xl font-bold tracking-tight ${getStatusColor()}`}>
          {value}
        </div>
        <div className="text-xs text-text-muted mt-2 leading-snug font-medium max-w-[220px]">
          {description}
        </div>
      </div>
    </div>
  );
}

export function DeviceRiskCard({ aScore, status }) {
  return (
    <RiskCard
      title="DEVICE RISK"
      icon={Activity}
      value={aScore}
      status={status}
      description="Current-state abnormality evidence (A_SCORE)"
    />
  );
}

export function FutureRiskCard({ predictionRisk, status }) {
  return (
    <RiskCard
      title="FUTURE RISK"
      icon={TrendingUp}
      value={predictionRisk}
      status={status}
      description="Projected degradation & engineering-limit proximity"
    />
  );
}

export function TestIntegrityCard({ quality, status }) {
  return (
    <RiskCard
      title="TEST INTEGRITY"
      icon={Shield}
      value={quality}
      status={status}
      description="Measurement trustworthiness"
    />
  );
}
