"""
Unit tests for FastAPI prediction server
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

from api.prediction_server import app


@pytest.fixture
def client():
    return TestClient(app)


def test_root_endpoint(client):
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "service" in response.json()


def test_health_check_no_model(client):
    """Test health check when model is not loaded"""
    response = client.get("/health")
    assert response.status_code == 503


def test_metrics_endpoint(client):
    """Test Prometheus metrics endpoint"""
    response = client.get("/metrics")
    assert response.status_code == 200

