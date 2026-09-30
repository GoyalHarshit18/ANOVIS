import React, { useEffect, useState } from 'react';
import { Search, Bell, ChevronDown } from 'lucide-react';
import { apiService } from '../../services/apiService';
import { DEMO_IDENTIFIERS } from '../../data/demoFallbacks';

const DEFAULT_LOTS = [
  { lot_id: 'LOT_PRED_TEST_01', device_type: 'TYPE_B' }
];

export default function Header() {
  const [lot, setLot] = useState(DEMO_IDENTIFIERS.lot);
  const [device, setDevice] = useState(DEMO_IDENTIFIERS.deviceType);
  const [lotsList, setLotsList] = useState(DEFAULT_LOTS);

  useEffect(() => {
    async function fetchLots() {
      try {
        const lotsData = await apiService.getLots().catch(() => ({ lots: [] }));
        let list = (lotsData?.lots && lotsData.lots.length > 0) ? [...lotsData.lots] : [];

        // Also check components for any unique lots
        const compsData = await apiService.getComponents().catch(() => ({ results: [] }));
        if (compsData?.results?.length > 0) {
          compsData.results.forEach(c => {
            if (c.lot && !list.some(item => item.lot_id === c.lot)) {
              list.push({ lot_id: c.lot, device_type: c.device_type || 'TYPE_B' });
            }
          });
        }

        if (list.length === 0) {
          list = DEFAULT_LOTS;
        }

        setLotsList(list);

        // Check if there is a previously selected lot in localStorage or default to first
        const savedLotId = localStorage.getItem('selectedLotId');
        const initialLotObj = (savedLotId && list.find(l => l.lot_id === savedLotId)) || list[0];
        
        const activeLotId = initialLotObj?.lot_id || DEMO_IDENTIFIERS.lot;
        const activeDevice = initialLotObj?.device_type || DEMO_IDENTIFIERS.deviceType;
        
        setLot(activeLotId);
        setDevice(activeDevice);
      } catch (e) {
        console.error("Failed to load lots for header", e);
        setLotsList(DEFAULT_LOTS);
        setLot(DEMO_IDENTIFIERS.lot);
        setDevice(DEMO_IDENTIFIERS.deviceType);
      }
    }
    fetchLots();
  }, []);

  const handleLotChange = (newLotId) => {
    const found = lotsList.find(l => l.lot_id === newLotId);
    const newDevice = found?.device_type || 'TYPE_B';
    setLot(newLotId);
    setDevice(newDevice);
    localStorage.setItem('selectedLotId', newLotId);

    // Dispatch global custom event so all pages (Dashboard, Anomaly, etc.) can react immediately
    window.dispatchEvent(new CustomEvent('appLotChanged', {
      detail: { lotId: newLotId, deviceType: newDevice }
    }));
  };

  return (
    <header className="h-[60px] bg-bg-surface border-b border-border-default flex items-center px-6 justify-between z-10 relative">
      <div className="flex items-center gap-4">
        {/* INTERACTIVE LOT SELECTOR */}
        <div className="bg-bg-surface-alt px-3 py-1.5 rounded-[4px] border border-border-default flex items-center shadow-sm relative">
          <span className="text-text-secondary text-[10px] font-bold tracking-wider uppercase mr-2 shrink-0">LOT</span>
          <div className="relative flex items-center">
            <select
              value={lot}
              onChange={(e) => handleLotChange(e.target.value)}
              className="bg-transparent font-mono text-xs text-text-primary font-bold border-none outline-none cursor-pointer pr-5 appearance-none focus:ring-1 focus:ring-accent-primary rounded"
            >
              {lotsList.map(l => (
                <option key={l.lot_id} value={l.lot_id} className="bg-white text-slate-800 font-mono text-xs">
                  {l.lot_id}
                </option>
              ))}
            </select>
            <ChevronDown size={12} className="text-text-muted absolute right-0 pointer-events-none" />
          </div>
        </div>

        {/* DEVICE TYPE BADGE */}
        <div className="bg-bg-surface-alt px-3 py-1.5 rounded-[4px] border border-border-default flex items-center shadow-sm">
          <span className="text-text-secondary text-[10px] font-bold tracking-wider uppercase">DEVICE</span>
          <span className="font-mono text-xs ml-2 text-text-primary font-semibold">{device}</span>
        </div>
      </div>
      
      <div className="flex items-center gap-6">
        <div className="flex items-center bg-white border border-border-strong rounded-[6px] px-3 py-1.5 w-[260px] gap-2 focus-within:border-accent-primary focus-within:ring-2 focus-within:ring-accent-soft transition-all shadow-sm">
          <Search size={14} className="text-text-muted" />
          <input 
            type="text" 
            placeholder="Search component ID..." 
            className="bg-transparent border-none text-text-primary outline-none w-full font-mono text-xs placeholder:text-text-muted" 
          />
        </div>
        
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-status-pass"></div>
          <span className="text-[11px] font-mono font-bold text-text-secondary">API: ONLINE</span>
        </div>
        
        <button className="bg-transparent border border-border-default text-text-secondary cursor-pointer flex items-center justify-center p-1.5 rounded-[4px] transition-colors hover:bg-bg-surface-alt hover:text-text-primary shadow-sm">
          <Bell size={16} />
        </button>
      </div>
    </header>
  );
}
