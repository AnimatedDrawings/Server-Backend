import pytest
from fastapi.testclient import TestClient
from ad_fast_api.main import app


@pytest.fixture(scope="session")
def test_client():
    client = TestClient(app)
    return client
