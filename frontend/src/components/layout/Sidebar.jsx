import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { LayoutDashboard, FileSearch, Layers, Cpu, Activity, Settings, BrainCircuit, FileText } from 'lucide-react';

const navItems = [
  { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/screening', label: 'Screening', icon: FileSearch },
  { path: '/explainability', label: 'Explainability & QA', icon: BrainCircuit }
];


export default function Sidebar() {
  const location = useLocation();

  return (
    <div className="w-[260px] bg-bg-surface border-r border-border-default flex flex-col transition-all duration-200 shrink-0 hidden md:flex z-10 relative">
      <div className="p-6 pb-4 border-b border-border-default mb-4">
        <div className="flex items-center gap-2">
          <Cpu className="text-accent-primary" size={24} />
          <span className="font-bold text-lg tracking-[0.1em] text-text-primary uppercase">Anovis</span>
        </div>
        <div className="font-mono text-[10px] text-text-muted mt-1 uppercase tracking-widest font-semibold">COMMAND CENTER</div>
      </div>
      
      <nav className="flex flex-col px-3 flex-1 gap-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname.startsWith(item.path);
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={`flex items-center gap-3 px-3 py-2 rounded-[4px] transition-colors text-[13px] font-medium ${
                isActive 
                  ? 'bg-accent-soft text-accent-primary border-l-2 border-accent-primary pl-[10px]' 
                  : 'text-text-secondary hover:bg-[#F1F5F9] hover:text-text-primary pl-3'
              }`}
            >
              <Icon size={18} strokeWidth={isActive ? 2.5 : 2} />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>
      
      <div className="p-6 border-t border-border-default mt-auto">
        <div className="text-[11px] text-text-muted font-mono tracking-wider">v3.0.0 (Hardened)</div>
      </div>
    </div>
  );
}
