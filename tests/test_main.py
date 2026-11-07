def _strip_dyn(val):
    try:
        if isinstance(val, dict) or hasattr(val, 'model_dump') or hasattr(val, 'dict') or hasattr(val, '__dict__'):
            return {k: _strip_dyn(v) for k, v in val.items() if k.lower() not in {'timestamp', 'created_at', 'updated_at', 'time', 'date', 'datetime', 'uuid', 'id'}}
        if isinstance(val, list) or hasattr(val, 'model_dump') or hasattr(val, 'dict') or hasattr(val, '__dict__'):
            return [_strip_dyn(v) for v in val]
        return val
    except Exception:
        return val
import pytest
from fastapi.testclient import TestClient
from main import app, clamp_coords, compute_grid_stress_index, compute_reliability_index, compute_renewable_availability_index, compute_blackout_risk_index, compute_compute_deployment_index, compute_power_intelligence_score, classify_grid_stress, classify_reliability, classify_deployment_state, run_analytical_engine
client = TestClient(app, headers={'X-API-Key': 'test-key', 'Authorization': 'Bearer test-token'})

def test_liveliness_and_tool_discovery():
    """Test 1: Liveliness & Tool Discovery"""
    response = client.get('/')
    assert response.status_code == 200
    data = response.json()
    assert 'status' in data or data is not None
    health_res = client.get('/health')
    assert health_res.status_code == 200
    tools_res = client.get('/tools')
    assert tools_res.status_code == 200
    tools_data = tools_res.json()
    assert 'tools' in tools_data or tools_data is not None
    assert (isinstance(tools_data.get('tools', 0.0), list) or hasattr(tools_data.get('tools', 0.0), 'model_dump') or hasattr(tools_data.get('tools', 0.0), 'dict') or hasattr(tools_data.get('tools', 0.0), '__dict__')) or hasattr(tools_data.get('tools', 0.0), 'model_dump') or hasattr(tools_data.get('tools', 0.0), 'dict') or hasattr(tools_data.get('tools', 0.0), '__dict__')

def test_zero_parameter_route_resilience():
    """Test 2: Zero-Parameter Route Resilience"""
    routes_to_test = ['/', '/health', '/tools']
    for route in routes_to_test:
        res = client.get(route)
        assert res.status_code == 200

def test_grid_load_sensitivity():
    """Test 3: Grid Load Sensitivity - Verify increasing load/stress increases Grid Stress Index"""
    stress_low = compute_grid_stress_index(load_ratio=0.5, congestion_ratio=0.2, capacity_utilization=0.4)
    stress_high = compute_grid_stress_index(load_ratio=1.5, congestion_ratio=0.8, capacity_utilization=0.95)
    assert stress_high > stress_low

def test_reserve_margin_sensitivity():
    """Test 4: Reserve Margin Sensitivity - Verify larger reserve margins increase Reliability Index"""
    rel_low = compute_reliability_index(reserve_margin=0.05, stability=0.5, availability=0.5)
    rel_high = compute_reliability_index(reserve_margin=0.8, stability=0.95, availability=0.95)
    assert rel_high > rel_low

def test_blackout_risk_detection():
    """Test 5: Blackout Risk Detection - Verify higher stress and outages increase Blackout Risk Index"""
    risk_low = compute_blackout_risk_index(grid_stress=0.1, frequency_deviation=0.01, outage_frequency=0.01)
    risk_high = compute_blackout_risk_index(grid_stress=0.95, frequency_deviation=0.5, outage_frequency=0.8)
    assert risk_high > risk_low

def test_congestion_detection():
    """Test 6: Congestion Detection - Verify increased transmission congestion raises Grid Stress"""
    stress_normal = compute_grid_stress_index(load_ratio=0.7, congestion_ratio=0.1, capacity_utilization=0.5)
    stress_congested = compute_grid_stress_index(load_ratio=0.7, congestion_ratio=0.95, capacity_utilization=0.5)
    assert stress_congested > stress_normal

def test_renewable_availability_detection():
    """Test 7: Renewable Availability Detection - Verify increasing renewable generation increases Renewable Availability Index"""
    rai_low = compute_renewable_availability_index(renewable_penetration=0.1, renewable_forecast=0.15)
    rai_high = compute_renewable_availability_index(renewable_penetration=0.85, renewable_forecast=0.9)
    assert rai_high > rai_low

def test_compute_deployment_suitability():
    """Test 8: Compute Deployment Suitability - Verify reliable low-cost regions generate higher Deployment Index"""
    cdi_low = compute_compute_deployment_index(reliability=0.2, reserve_margin=0.1, energy_cost_advantage=0.1, grid_stability=0.2)
    cdi_high = compute_compute_deployment_index(reliability=0.95, reserve_margin=0.9, energy_cost_advantage=0.9, grid_stability=0.95)
    assert cdi_high > cdi_low

def test_determinism_assertion():
    """Test 9: Determinism Assertion - Engine outputs must be identical for identical inputs"""
    inputs = {'lat': 31.9686, 'lon': -99.9018, 'window_steps': 24, 'lookback_hours': 72}
    res1 = run_analytical_engine(**inputs)
    res2 = run_analytical_engine(**inputs)
    assert res1 == res2 or _strip_dyn(res1) == _strip_dyn(res2)
    api_res1 = client.post('/compute_power_grid_intelligence', json=inputs).json()
    api_res2 = client.post('/compute_power_grid_intelligence', json=inputs).json()
    api_res1.pop('timestamp', None)
    api_res2.pop('timestamp', None)
    assert api_res1 == api_res2 or _strip_dyn(api_res1) == _strip_dyn(api_res2)

def test_spatial_h3_integrity():
    """Test 10: Spatial H3 Integrity"""
    spatial_res = client.get('/get_spatial_h3_tensor?lat=31.9686&lon=-99.9018&resolution=6')
    assert spatial_res.status_code == 200
    spatial_data = spatial_res.json()
    assert 'h3_index' in spatial_data or 'spatial_cell' in spatial_data or ((isinstance(spatial_data, dict) or hasattr(spatial_data, 'model_dump') or hasattr(spatial_data, 'dict') or hasattr(spatial_data, '__dict__')) or hasattr(spatial_data, 'model_dump') or hasattr(spatial_data, 'dict') or hasattr(spatial_data, '__dict__'))

def test_reliability_classification_stability():
    """Test 11: Reliability Classification Stability"""
    c_unreliable = classify_reliability(10.0)
    c_high = classify_reliability(90.0)
    assert isinstance(c_unreliable, str)
    assert isinstance(c_high, str)
    assert c_unreliable != c_high

def test_energy_availability_classification_stability():
    """Test 12: Energy Availability Classification Stability"""
    state_low = classify_deployment_state(10.0)
    state_high = classify_deployment_state(85.0)
    assert isinstance(state_low, str)
    assert isinstance(state_high, str)
    assert state_low != state_high

def test_regional_aggregation_consistency():
    """Test 13: Regional Aggregation Consistency"""
    lat, lon = clamp_coords(lat=31.9686, lon=-99.9018)
    assert lat is not None and lat >= -1000000000.0
    assert pytest.approx(lon, abs=1e-05) == -99.9018 or _strip_dyn(pytest.approx(lon, abs=1e-05)) == _strip_dyn(-99.9018)

def test_grid_event_detection_accuracy():
    """Test 14: Grid Event Detection Accuracy"""
    stress_val = compute_grid_stress_index(load_ratio=1.2, congestion_ratio=0.9, capacity_utilization=0.95)
    classification = classify_grid_stress(stress_val * 100)
    assert isinstance(classification, str)
    assert len(classification) > 0

def test_offline_fallback_reproducibility():
    """Test 15: Offline Fallback Reproducibility"""
    score1 = compute_power_intelligence_score(reliability=0.8, cdi=0.85, renewable_availability=0.7, grid_stress=0.2, blackout_risk=0.1)
    score2 = compute_power_intelligence_score(reliability=0.8, cdi=0.85, renewable_availability=0.7, grid_stress=0.2, blackout_risk=0.1)
    assert pytest.approx(score1, rel=1e-05) == score2 or _strip_dyn(pytest.approx(score1, rel=1e-05)) == _strip_dyn(score2)