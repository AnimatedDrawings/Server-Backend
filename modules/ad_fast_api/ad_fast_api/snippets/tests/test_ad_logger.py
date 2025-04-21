from ad_fast_api.snippets.sources.ad_logger import setup_logger, LOG_FILE_NAME
from pathlib import Path


def test_logger():
    # given
    test_dir = Path(__file__).parent
    logger = setup_logger(ad_id="test", base_path=test_dir)

    # when
    logger.error("test")

    # then
    log_file = test_dir.joinpath(LOG_FILE_NAME)
    assert log_file.is_file()

    with open(log_file, "r") as f:
        assert "test" in f.read()

    # teardown
    log_file.unlink()
