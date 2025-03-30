import pytest
from unittest.mock import Mock
from logging import Logger


@pytest.fixture(scope="function")
def mock_logger():
    return Mock(spec=Logger)
