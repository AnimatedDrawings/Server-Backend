import pytest
from fastapi.testclient import TestClient
from ad_fast_api.main import app


@pytest.fixture
def mock_client():
    return TestClient(app)
