import React from 'react';
import { CheckCircle, AlertTriangle, AlertOctagon, RefreshCcw, Eye, HelpCircle } from 'lucide-react';

const DECISION_CONFIG = {
  PASS: { icon: CheckCircle, classes: 'bg-status-pass-bg text-status-pass border-status-pass-border' },
  MONITOR: { icon: Eye, classes: 'bg-status-monitor-bg text-status-monitor border-status-monitor-border' },
  REVIEW: { icon: AlertTriangle, classes: 'bg-status-review-bg text-status-review border-status-review-border' },
  REJECT: { icon: AlertOctagon, classes: 'bg-status-reject-bg text-status-reject border-status-reject-border' },
  REPEAT_MEASUREMENT: { icon: RefreshCcw, classes: 'bg-status-repeat-bg text-status-repeat border-status-repeat-border' },
  REVIEW_REQUIRED: { icon: AlertTriangle, classes: 'bg-[#FFF0E3] text-[#B95700] border-[#FCD9BE]' },
  DATA_UNAVAILABLE: { icon: HelpCircle, classes: 'bg-[#F1F5F9] text-[#526171] border-[#D8E0E8]' }
};

export function DecisionBadge({ decision, size = 'normal' }) {
  const config = DECISION_CONFIG[decision] || DECISION_CONFIG.DATA_UNAVAILABLE;
  const Icon = config.icon;
  
  const sizeClasses = size === 'large' 
    ? 'px-4 py-1.5 text-[13px] rounded-[4px]' 
    : 'px-2 py-1 text-[11px] rounded-[4px]';

  return (
    <div className={`inline-flex items-center font-bold tracking-[0.05em] gap-1.5 border ${sizeClasses} ${config.classes}`}>
      <Icon size={size === 'large' ? 16 : 12} strokeWidth={2.5} />
      <span>{decision.replace('_', ' ')}</span>
    </div>
  );
}

const STATUS_CONFIG = {
  NORMAL: { classes: 'bg-status-pass-bg text-status-pass border border-status-pass-border' },
  ELEVATED: { classes: 'bg-status-monitor-bg text-status-monitor border border-status-monitor-border' },
  HIGH: { classes: 'bg-status-review-bg text-status-review border border-status-review-border' },
  DETECTED: { classes: 'bg-status-reject-bg text-status-reject border border-status-reject-border' },
  'NOT DETECTED': { classes: 'bg-status-pass-bg text-status-pass border border-status-pass-border' },
  PASS: { classes: 'bg-status-pass-bg text-status-pass border border-status-pass-border' },
  FAIL: { classes: 'bg-status-review-bg text-status-review border border-status-review-border' },
  LOW: { classes: 'bg-status-monitor-bg text-status-monitor border border-status-monitor-border' }
};

export function StatusBadge({ status }) {
  if (!status || status === 'N/A') return <span className="text-text-muted font-mono text-xs">N/A</span>;
  
  const config = STATUS_CONFIG[status.toUpperCase()] || { classes: 'bg-[#F1F5F9] text-[#526171] border border-[#D8E0E8]' };
  
  return (
    <div className={`inline-flex items-center px-2 py-0.5 rounded-[4px] text-[10px] font-bold uppercase tracking-[0.06em] ${config.classes}`}>
      {status}
    </div>
  );
}
