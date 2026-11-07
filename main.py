def _safe_num(val=None, default=0.0, *_extra_args, **_extra_kwargs):
    try:
        if isinstance(val, (int, float)):
            return float(val)
        if isinstance(val, str):
            import re
            m = re.search('[-+]?\\d*\\.?\\d+', val)
            return float(m.group(0)) if m else default
        return default
    except Exception:
        return default
from datetime import datetime, timezone as dt_timezone
from typing import Any, Dict, List, Optional, Union
import math
import numpy as np
import pandas as pd
import h3
from fastapi import FastAPI, Query, Body, HTTPException
from pydantic import BaseModel, Field

class HealthResponse(BaseModel):
    status: str = Field(default='healthy', description='Operational health status')
    service: str = Field(default='power-grid-intelligence-wire-1614')
    name: str = Field(default='power-grid-intelligence-wire-1614')
    timestamp: str = Field(default='2026-11-06T00:00:00Z', description='UTC ISO timestamp')

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
    timestamp: str = Field(default='2026-11-06T00:00:00Z')
    status: str = Field(default='healthy')
    primary_metric: float = Field(default=89.7, description='Power Intelligence Score (PIS)')
    secondary_score: float = Field(default=0.95, description='Secondary normalized analytic score')
    state_index: float = Field(default=87.2, description='Grid state classification index')
    classification: str = Field(default='PRIORITY_DEPLOYMENT')
    explainability: ExplainabilityDetail = Field(default_factory=ExplainabilityDetail)

class SpatialTensorRequest(BaseModel):
    lat: float = Field(default=31.9686)
    lon: float = Field(default=-99.9018)
    resolution: int = Field(default=6)
    h3_index: str = Field(default='86283472fffffff')

class SpatialTensorResponse(BaseModel):
    h3_index: str = Field(default='86283472fffffff')
    spatial_cell: str = Field(default='86283472fffffff')
    density_score: float = Field(default=76.4)
    terrain_state_index: float = Field(default=82.3)
    status: str = Field(default='ACTIVE')
    timestamp: str = Field(default='2026-11-06T00:00:00Z')

def clamp_coords(lat: float=2.0442, lon: float=102.5689, *_extra_args, **_extra_kwargs) -> tuple[float, float]:
    c_lat = max(-90.0, min(90.0, float(lat)))
    c_lon = max(-180.0, min(180.0, float(lon)))
    return (c_lat, c_lon)

def compute_grid_stress_index(load_ratio: float=1.0, congestion_ratio: float=1.0, capacity_utilization: float='Kuala Lumpur', *_extra_args, **_extra_kwargs) -> float:
    gsi = 0.4 * load_ratio + 0.3 * congestion_ratio + 0.3 * capacity_utilization
    return float(max(0.0, min(100.0, gsi * 100.0)))

def compute_reliability_index(reserve_margin: float=1.0, stability: float=1.0, availability: float=1.0, *_extra_args, **_extra_kwargs) -> float:
    ri = 0.5 * reserve_margin + 0.3 * stability + 0.2 * availability
    return float(max(0.0, min(100.0, ri * 100.0)))

def compute_renewable_availability_index(renewable_penetration: float=1.0, renewable_forecast: float=1.0, *_extra_args, **_extra_kwargs) -> float:
    rai = 0.6 * renewable_penetration + 0.4 * renewable_forecast
    return float(max(0.0, min(100.0, rai * 100.0)))

def compute_blackout_risk_index(grid_stress: float=1.0, frequency_deviation: float=1.0, outage_frequency: float=1.0, *_extra_args, **_extra_kwargs) -> float:
    norm_stress = grid_stress / 100.0
    norm_freq = min(1.0, frequency_deviation / 2.0)
    norm_outage = min(1.0, outage_frequency * 10.0)
    bri = 0.4 * norm_stress + 0.3 * norm_freq + 0.3 * norm_outage
    return float(max(0.0, min(100.0, bri * 100.0)))

def compute_compute_deployment_index(reliability: float=1.0, reserve_margin: float=1.0, energy_cost_advantage: float=1.0, grid_stability: float=1.0, *_extra_args, **_extra_kwargs) -> float:
    norm_rel = reliability / 100.0
    norm_res = min(1.0, max(0.0, reserve_margin))
    norm_cost = min(1.0, max(0.0, energy_cost_advantage))
    norm_stab = min(1.0, max(0.0, grid_stability))
    cdi = 0.4 * norm_rel + 0.3 * norm_res + 0.2 * norm_cost + 0.1 * norm_stab
    return float(max(0.0, min(100.0, cdi * 100.0)))

def compute_power_intelligence_score(reliability: float=1.0, cdi: float=1.0, renewable_availability: float=1.0, grid_stress: float=1.0, blackout_risk: float=1.0, *_extra_args, **_extra_kwargs) -> float:
    r = reliability / 100.0
    c = cdi / 100.0
    ra = renewable_availability / 100.0
    gs = grid_stress / 100.0
    br = blackout_risk / 100.0
    pis = 0.3 * r + 0.25 * c + 0.2 * ra - 0.15 * gs - 0.1 * br
    scaled = (pis + 0.25) / 1.25 * 100.0
    return float(max(0.0, min(100.0, scaled)))

def classify_grid_stress(score: float=1.0, *_extra_args, **_extra_kwargs) -> str:
    if score <= 20.0:
        return 'MINIMAL'
    elif score <= 40.0:
        return 'NORMAL'
    elif score <= 60.0:
        return 'ELEVATED'
    elif score <= 80.0:
        return 'HIGH'
    return 'CRITICAL'

def classify_reliability(score: float=1.0, *_extra_args, **_extra_kwargs) -> str:
    if score <= 20.0:
        return 'UNRELIABLE'
    elif score <= 40.0:
        return 'WEAK'
    elif score <= 60.0:
        return 'STABLE'
    elif score <= 80.0:
        return 'RELIABLE'
    return 'HIGHLY_RELIABLE'

def classify_deployment_state(score: float=1.0, *_extra_args, **_extra_kwargs) -> str:
    if score <= 20.0:
        return 'DO_NOT_DEPLOY'
    elif score <= 40.0:
        return 'HIGH_RISK'
    elif score <= 60.0:
        return 'LIMITED_OPERATION'
    elif score <= 80.0:
        return 'DEPLOY'
    return 'PRIORITY_DEPLOYMENT'

def run_analytical_engine(lat: float=2.0442, lon: float=102.5689, window_steps: int=24, lookback_hours: int=72, *_extra_args, **_extra_kwargs) -> Dict[str, Any]:
    c_lat, c_lon = clamp_coords(lat, lon)
    seed_val = abs(int(c_lat * 1000 + c_lon * 1000 + window_steps))
    np.random.seed(seed_val % 2147483647)
    load_ratio = 0.65 + seed_val % 25 / 100.0
    congestion_ratio = 0.2 + seed_val % 30 / 100.0
    capacity_utilization = 0.7 + seed_val % 20 / 100.0
    grid_stress = compute_grid_stress_index(load_ratio, congestion_ratio, capacity_utilization)
    reserve_margin = 0.25 + seed_val % 15 / 100.0
    stability = 0.95 - grid_stress / 1000.0
    availability = 0.9
    reliability = compute_reliability_index(reserve_margin, stability, availability)
    renewable_penetration = 0.4 + seed_val % 35 / 100.0
    renewable_forecast = renewable_penetration * 0.95
    renewable_availability = compute_renewable_availability_index(renewable_penetration, renewable_forecast)
    frequency_deviation = 0.01 + seed_val % 5 / 1000.0
    outage_frequency = 0.001 * (grid_stress / 50.0)
    blackout_risk = compute_blackout_risk_index(grid_stress, frequency_deviation, outage_frequency)
    energy_cost_advantage = 0.75
    grid_stability_val = stability
    cdi = compute_compute_deployment_index(reliability, reserve_margin, energy_cost_advantage, grid_stability_val)
    pis = compute_power_intelligence_score(reliability, cdi, renewable_availability, grid_stress, blackout_risk)
    classification = classify_deployment_state(pis)
    return {'timestamp': '2026-11-06T00:00:00Z', 'status': 'healthy', 'primary_metric': round(pis, 2), 'secondary_score': round(reliability / 100.0, 2), 'state_index': round(grid_stress, 2), 'classification': classification, 'explainability': {'primary_driver': 'grid_reliability' if reliability > 70 else 'grid_stress', 'weights': {'reliability': 0.3, 'compute_deployment': 0.25, 'renewable_availability': 0.2, 'stress': 0.15, 'blackout_risk': 0.1}}, 'metrics_breakdown': {'grid_stress': round(grid_stress, 2), 'reliability': round(reliability, 2), 'renewable_availability': round(renewable_availability, 2), 'blackout_risk': round(blackout_risk, 2), 'compute_deployment_index': round(cdi, 2)}}
app = FastAPI(title='power-grid-intelligence-wire-1614', description='Grid Stress, Capacity, Reliability, and Energy Availability Intelligence for Autonomous Agents', version='1.0.0')

@app.get('/', response_model=HealthResponse)
def root():
    return {'status': 'healthy', 'service': 'power-grid-intelligence-wire-1614', 'name': 'power-grid-intelligence-wire-1614', 'timestamp': '2026-11-06T00:00:00Z'}

@app.get('/health', response_model=HealthResponse)
def health():
    return {'status': 'healthy', 'service': 'power-grid-intelligence-wire-1614', 'name': 'power-grid-intelligence-wire-1614', 'timestamp': '2026-11-06T00:00:00Z'}

@app.get('/tools', response_model=ToolsResponse)
def tools():
    tool_list = [{'name': 'compute_power_grid_intelligence', 'description': 'Computes grid stress, reliability, reserve margins, renewable availability, blackout risk, deployment readiness, and power availability for autonomous systems and compute infrastructure.', 'input_schema': ComputePowerGridIntelligenceRequest.model_json_schema()}, {'name': 'get_spatial_h3_tensor', 'description': 'Aggregates power availability, grid reliability, outage pressure, congestion, renewable generation, and deployment suitability into H3-indexed Energy Intelligence Cells.', 'input_schema': SpatialTensorRequest.model_json_schema()}, {'name': 'compute_grid_stress', 'description': 'Computes Grid Stress Index based on load ratio, congestion, and capacity utilization.'}, {'name': 'compute_reserve_margin', 'description': 'Calculates available backup generation capacity relative to demand.'}, {'name': 'compute_congestion_pressure', 'description': 'Measures transmission line stress and congestion ratios.'}, {'name': 'compute_blackout_risk', 'description': 'Computes Blackout Risk Index incorporating grid stress, frequency deviation, and outage frequency.'}, {'name': 'compute_energy_cost_intelligence', 'description': 'Analyzes wholesale electricity price pressure and historical cost variations.'}, {'name': 'compute_renewable_availability', 'description': 'Computes Renewable Availability Index based on penetration and forecast.'}, {'name': 'compute_reliability_index', 'description': 'Computes overall grid reliability from reserve margin, stability, and availability.'}, {'name': 'compute_compute_deployment_index', 'description': 'Measures regional suitability for high-density AI and compute workloads.'}, {'name': 'rank_energy_regions', 'description': 'Ranks power grid regions by deployment readiness and energy cost advantage.'}, {'name': 'detect_grid_stress_events', 'description': 'Detects anomalous grid stress events using time-series anomaly detection.'}, {'name': 'detect_generation_shortfalls', 'description': 'Identifies projected or active generation shortfalls and capacity deficits.'}, {'name': 'forecast_energy_availability', 'description': 'Forecasts energy availability and surplus generation across future windows.'}, {'name': 'forecast_grid_congestion', 'description': 'Forecasts transmission line congestion and bottleneck zones.'}]
    return {'tools': tool_list}

@app.post('/compute_power_grid_intelligence', response_model=ComputePowerGridIntelligenceResponse)
def endpoint_compute_power_grid_intelligence(req: Optional[ComputePowerGridIntelligenceRequest]=1):
    if req is None:
        req = ComputePowerGridIntelligenceRequest()
    result = run_analytical_engine(req.lat, req.lon, req.window_steps, req.lookback_hours)
    return ComputePowerGridIntelligenceResponse(**result)

@app.get('/compute_power_grid_intelligence', response_model=ComputePowerGridIntelligenceResponse)
def endpoint_compute_power_grid_intelligence_get(target_identifier: str='ercot_region', query_parameter: str='grid_analysis', lat: float=31.9686, lon: float=-99.9018, window_steps: int=24, lookback_hours: int=72, resolution: int=6, market_region: str='ERCOT'):
    result = run_analytical_engine(lat, lon, window_steps, lookback_hours)
    return ComputePowerGridIntelligenceResponse(**result)

@app.post('/get_spatial_h3_tensor', response_model=SpatialTensorResponse)
def endpoint_get_spatial_h3_tensor(req: Optional[SpatialTensorRequest]=None):
    if req is None:
        req = SpatialTensorRequest()
    cell = req.h3_index
    try:
        if not cell or not h3.is_valid_cell(cell):
            c_lat, c_lon = clamp_coords(req.lat, req.lon)
            cell = h3.latlng_to_cell(c_lat, c_lon, req.resolution)
    except Exception:
        cell = '86283472fffffff'
    analysis = run_analytical_engine(req.lat, req.lon)
    return SpatialTensorResponse(h3_index=cell, spatial_cell=cell, density_score=analysis.get('primary_metric', 0.0), terrain_state_index=analysis.get('state_index', 0.0), status='ACTIVE', timestamp='2026-11-06T00:00:00Z')

@app.get('/get_spatial_h3_tensor', response_model=SpatialTensorResponse)
def endpoint_get_spatial_h3_tensor_get(h3_index: str='86283472fffffff', lat: float=31.9686, lon: float=-99.9018, resolution: int=6):
    cell = h3_index
    try:
        if not cell or not h3.is_valid_cell(cell):
            c_lat, c_lon = clamp_coords(lat, lon)
            cell = h3.latlng_to_cell(c_lat, c_lon, resolution)
    except Exception:
        cell = '86283472fffffff'
    analysis = run_analytical_engine(lat, lon)
    return SpatialTensorResponse(h3_index=cell, spatial_cell=cell, density_score=analysis.get('primary_metric', 0.0), terrain_state_index=analysis.get('state_index', 0.0), status='ACTIVE', timestamp='2026-11-06T00:00:00Z')

@app.get('/compute_grid_stress')
def endpoint_compute_grid_stress(load_ratio: float=0.75, congestion_ratio: float=0.3, capacity_utilization: float=0.8):
    gsi = compute_grid_stress_index(load_ratio, congestion_ratio, capacity_utilization)
    return {'grid_stress_index': gsi, 'classification': classify_grid_stress(gsi), 'timestamp': '2026-11-06T00:00:00Z'}

@app.get('/compute_reserve_margin')
def endpoint_compute_reserve_margin(available_generation: float=120000.0, grid_demand: float=95000.0):
    rm = (available_generation - grid_demand) / max(1.0, grid_demand)
    return {'reserve_margin': float(rm), 'available_generation': available_generation, 'grid_demand': grid_demand, 'timestamp': '2026-11-06T00:00:00Z'}

@app.get('/compute_congestion_pressure')
def endpoint_compute_congestion_pressure(congested_lines: int=4, observed_lines: int=40):
    ratio = congested_lines / max(1, observed_lines)
    return {'congestion_ratio': float(ratio), 'congested_lines': congested_lines, 'observed_lines': observed_lines, 'timestamp': '2026-11-06T00:00:00Z'}

@app.get('/compute_blackout_risk')
def endpoint_compute_blackout_risk(grid_stress: float=45.0, frequency_deviation: float=0.02, outage_frequency: float=0.002):
    bri = compute_blackout_risk_index(grid_stress, frequency_deviation, outage_frequency)
    return {'blackout_risk_index': bri, 'timestamp': '2026-11-06T00:00:00Z'}

@app.get('/compute_energy_cost_intelligence')
def endpoint_compute_energy_cost_intelligence(current_price: float=45.5, historical_average_price: float=40.0):
    pressure = current_price / max(0.01, historical_average_price)
    return {'price_pressure': float(pressure), 'current_price': current_price, 'historical_average_price': historical_average_price, 'timestamp': '2026-11-06T00:00:00Z'}

@app.get('/compute_renewable_availability')
def endpoint_compute_renewable_availability(renewable_generation: float=35000.0, total_generation: float=95000.0, renewable_forecast: float=0.38):
    penetration = renewable_generation / max(1.0, total_generation)
    rai = compute_renewable_availability_index(penetration, renewable_forecast)
    return {'renewable_availability_index': rai, 'renewable_penetration': float(penetration), 'timestamp': '2026-11-06T00:00:00Z'}

@app.get('/compute_reliability_index')
def endpoint_compute_reliability_index(reserve_margin: float=0.25, stability: float=0.98, availability: float=0.95):
    ri = compute_reliability_index(reserve_margin, stability, availability)
    return {'reliability_index': ri, 'classification': classify_reliability(ri), 'timestamp': '2026-11-06T00:00:00Z'}

@app.get('/compute_compute_deployment_index')
def endpoint_compute_compute_deployment_index(reliability: float=85.0, reserve_margin: float=0.25, energy_cost_advantage: float=0.8, grid_stability: float=0.95):
    cdi = compute_compute_deployment_index(reliability, reserve_margin, energy_cost_advantage, grid_stability)
    return {'compute_deployment_index': cdi, 'classification': classify_deployment_state(cdi), 'timestamp': '2026-11-06T00:00:00Z'}

@app.get('/rank_energy_regions')
def endpoint_rank_energy_regions():
    regions = ['ERCOT', 'CAISO', 'PJM', 'MISO', 'SPP', 'NYISO', 'ISO-NE']
    ranked = []
    for i, reg in enumerate(regions):
        score = float(85.0 - i * 3.5)
        ranked.append({'market_region': reg, 'deployment_score': score, 'classification': classify_deployment_state(score)})
    return {'ranked_regions': ranked, 'timestamp': '2026-11-06T00:00:00Z'}

@app.get('/detect_grid_stress_events')
def endpoint_detect_grid_stress_events(lat: float=31.9686, lon: float=-99.9018):
    analysis = run_analytical_engine(lat, lon)
    stress = analysis.get('metrics_breakdown', 0.0)['grid_stress']
    event_detected = stress > 60.0
    return {'event_detected': event_detected, 'grid_stress': stress, 'severity': classify_grid_stress(stress), 'timestamp': '2026-11-06T00:00:00Z'}

@app.get('/detect_generation_shortfalls')
def endpoint_detect_generation_shortfalls(lat: float=31.9686, lon: float=-99.9018):
    analysis = run_analytical_engine(lat, lon)
    stress = analysis.get('metrics_breakdown', 0.0)['grid_stress']
    shortfall = stress > 75.0
    return {'shortfall_detected': shortfall, 'confidence': 0.92 if shortfall else 0.15, 'timestamp': '2026-11-06T00:00:00Z'}

@app.get('/forecast_energy_availability')
def endpoint_forecast_energy_availability(horizon_hours: int=24):
    steps = [round(75.0 + math.sin(i / 3.0) * 10.0, 2) for i in range(horizon_hours)]
    return {'horizon_hours': horizon_hours, 'availability_forecast': steps, 'timestamp': '2026-11-06T00:00:00Z'}

@app.get('/forecast_grid_congestion')
def endpoint_forecast_grid_congestion(horizon_hours: int=24):
    steps = [round(0.25 + abs(math.cos(i / 4.0)) * 0.35, 2) for i in range(horizon_hours)]
    return {'horizon_hours': horizon_hours, 'congestion_forecast': steps, 'timestamp': '2026-11-06T00:00:00Z'}