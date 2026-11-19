import pytest
from app.core.pricing import estimate_cost

def test_cost_estimation_gpt4o():
    # gpt-4o: $2.50 / 1M in, $10.00 / 1M out
    # 1000 in = $0.0025, 500 out = $0.0050, total = $0.0075
    cost = estimate_cost("gpt-4o", input_tokens=1000, output_tokens=500)
    assert cost == 0.0075

def test_cost_estimation_mock_model():
    cost = estimate_cost("mock-gpt-4o", input_tokens=2000, output_tokens=1000)
    assert cost > 0.0
