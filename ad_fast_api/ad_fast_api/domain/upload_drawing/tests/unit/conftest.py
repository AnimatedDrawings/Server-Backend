import pytest
from ad_fast_api.snippets.sources.ad_logger import setup_logger
from ad_fast_api.main import app
from fastapi.testclient import TestClient
from ad_fast_api.domain.upload_drawing.testings import fake_upload_drawing as fud


@pytest.fixture(scope="session")
def mock_client():
    client = TestClient(app)
    yield client
    del client
