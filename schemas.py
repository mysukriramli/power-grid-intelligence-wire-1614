from datetime import timezone as dt_timezone
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field

class HealthResponse(BaseModel):
    status: str = Field(default='healthy', description='Operational health status')
    timestamp: str = Field(default_factory=lambda: datetime.now(dt_timezone.utc).isoformat(), description='UTC ISO timestamp')

class ToolItem(BaseModel):
    name: str = Field(default='', description='Tool identifier')
    description: str = Field(default='', description='Tool functional description')
    input_schema: Dict[str, Any] = Field(default_factory=dict, description='JSON schema for inputs')

class ToolsResponse(BaseModel):
    tools: List[Dict[str, Any]] = Field(default_factory=list, description='Registered agent tools')

class ComputePowerGridIntelligenceRequest(BaseModel):
    target_identifier: str = Field(default='ercot_region', description='Target region or asset identifier')
    query_parameter: str = Field(default='grid_analysis', description='Type of query or analytical focus')
    lat: float = Field(default=31.9686, description='Latitude coordinate clamped to [-90, 90]')
    lon: float = Field(default=-99.9018, description='Longitude coordinate clamped to [-180, 180]')
    window_steps: int = Field(default=24, description='Lookback or forecasting steps')
    lookback_hours: int = Field(default=72, description='Lookback hours for historical aggregation')
    resolution: int = Field(default=6, description='H3 spatial resolution [4, 9]')
    market_region: str = Field(default='ERCOT', description='Electricity market region code')

class ExplainabilityWeights(BaseModel):
    reliability: float = Field(default=0.3)
    compute_deployment: float = Field(default=0.25)
    renewable_availability: float = Field(default=0.2)
    stress: float = Field(default=0.15)
    blackout_risk: float = Field(default=0.1)

class ExplainabilityDetail(BaseModel):
    primary_driver: str = Field(default='grid_reliability')
    weights: ExplainabilityWeights = Field(default_factory=ExplainabilityWeights)

class ComputePowerGridIntelligenceResponse(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.now(dt_timezone.utc).isoformat())
    status: str = Field(default='healthy')
    primary_metric: float = Field(default=89.7, description='Power Intelligence Score (PIS)')
    secondary_score: float = Field(default=0.95, description='Secondary normalized analytical metric')
    state_index: float = Field(default=87.2, description='State classification index')
    classification: str = Field(default='PRIORITY_DEPLOYMENT', description='Agent deployment readiness state')
    explainability: ExplainabilityDetail = Field(default_factory=ExplainabilityDetail)

class GetSpatialH3TensorRequest(BaseModel):
    lat: float = Field(default=31.9686, description='Latitude coordinate clamped to [-90, 90]')
    lon: float = Field(default=-99.9018, description='Longitude coordinate clamped to [-180, 180]')
    resolution: int = Field(default=6, description='H3 spatial resolution [4, 9]')
    market_region: str = Field(default='ERCOT', description='Electricity market region code')

class GetSpatialH3TensorResponse(BaseModel):
    h3_index: str = Field(default='86283472fffffff', description='H3 spatial cell identifier')
    spatial_cell: str = Field(default='86283472fffffff', description='Duplicate spatial cell descriptor')
    density_score: float = Field(default=76.4, description='Grid stress or availability density score')
    terrain_state_index: float = Field(default=82.3, description='Reliability or terrain stability index')
    status: str = Field(default='ACTIVE', description='Spatial grid state status')

class GenericGridAnalysisRequest(BaseModel):
    lat: float = Field(default=31.9686, description='Latitude coordinate')
    lon: float = Field(default=-99.9018, description='Longitude coordinate')
    market_region: str = Field(default='ERCOT', description='Market region')
    lookback_hours: int = Field(default=72, description='Lookback window in hours')
    resolution: int = Field(default=6, description='H3 spatial resolution')

class GenericGridAnalysisResponse(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.now(dt_timezone.utc).isoformat())
    status: str = Field(default='success')
    metric_name: str = Field(default='grid_stress_index')
    value: float = Field(default=35.5)
    classification: str = Field(default='NORMAL')
    details: Dict[str, Any] = Field(default_factory=dict)

class RankEnergyRegionsRequest(BaseModel):
    regions: List[str] = Field(default_factory=lambda: ['ERCOT', 'CAISO', 'PJM', 'MISO', 'SPP'])
    metric: str = Field(default='compute_deployment_index')

class RankEnergyRegionsResponse(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.now(dt_timezone.utc).isoformat())
    rankings: List[Dict[str, Any]] = Field(default_factory=list)

class DetectGridEventsRequest(BaseModel):
    market_region: str = Field(default='ERCOT')
    lookback_hours: int = Field(default=24)
    threshold: float = Field(default=75.0)

class DetectGridEventsResponse(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.now(dt_timezone.utc).isoformat())
    events_detected: int = Field(default=0)
    events: List[Dict[str, Any]] = Field(default_factory=list)

class ForecastEnergyRequest(BaseModel):
    lat: float = Field(default=31.9686)
    lon: float = Field(default=-99.9018)
    horizon_hours: int = Field(default=24)
    resolution: int = Field(default=6)

class ForecastEnergyResponse(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.now(dt_timezone.utc).isoformat())
    forecast_horizon_hours: int = Field(default=24)
    predictions: List[Dict[str, Any]] = Field(default_factory=list)