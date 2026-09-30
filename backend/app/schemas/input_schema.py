"""Input schemas for the SIH26170 screening API."""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ComponentMeasurements(BaseModel):
    """Single component's burn-in measurements."""
    component_id: str = Field(..., description="Unique component identifier")
    lot_id: str = Field(default="LOT-2026-091", description="Lot identifier")
    device_type: str = Field(default="XYZ-IC", description="Device type")
    station: str = Field(default="ST-01", description="Test station")
    temperature: str = Field(default="125°C", description="Burn-in temperature")
    voltage: str = Field(default="3.3V", description="Test voltage")

    # Core 0h measurements
    Iddq_uA_0h: Optional[float] = Field(None, description="Iddq at 0h (µA)")
    Leakage_nA_0h: Optional[float] = Field(None, description="Leakage at 0h (nA)")
    PropDelay_ns_0h: Optional[float] = Field(None, description="Propagation delay at 0h (ns)")

    # 24h measurements
    Iddq_uA_24h: Optional[float] = Field(None, description="Iddq at 24h (µA)")
    Leakage_nA_24h: Optional[float] = Field(None, description="Leakage at 24h (nA)")
    PropDelay_ns_24h: Optional[float] = Field(None, description="Propagation delay at 24h (ns)")

    # Optional 96h measurements
    Iddq_uA_96h: Optional[float] = Field(None, description="Iddq at 96h (µA)")
    Leakage_nA_96h: Optional[float] = Field(None, description="Leakage at 96h (nA)")
    PropDelay_ns_96h: Optional[float] = Field(None, description="Propagation delay at 96h (ns)")

    # Optional 168h measurements (actual for comparison)
    Iddq_uA_168h: Optional[float] = Field(None, description="Iddq at 168h (µA)")
    Leakage_nA_168h: Optional[float] = Field(None, description="Leakage at 168h (nA)")
    PropDelay_ns_168h: Optional[float] = Field(None, description="Propagation delay at 168h (ns)")


class PredictRequest(BaseModel):
    """Prediction-only request."""
    component_id: str
    Iddq_uA_0h: float
    Iddq_uA_24h: float
    Leakage_nA_0h: float
    Leakage_nA_24h: float
    PropDelay_ns_0h: float
    PropDelay_ns_24h: float


class BatchScreenRequest(BaseModel):
    """Batch screening request with inline records."""
    records: List[ComponentMeasurements]
