import pytest
from ad_fast_api.snippets.sources.logger import setup_logger
from pathlib import Path


TEST_DIR = Path(__file__).parent
LOG_FILE_NAME = "test.log"


@pytest.fixture(scope="session")
def mock_logger():
    logger = setup_logger(
        base_path=TEST_DIR,
        log_file_name=LOG_FILE_NAME,
    )

    yield logger

    TEST_DIR.joinpath(LOG_FILE_NAME).unlink()
    del logger
