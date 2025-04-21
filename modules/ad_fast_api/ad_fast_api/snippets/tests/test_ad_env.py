import os
import pytest
from unittest.mock import patch
from ad_fast_api.snippets.sources.ad_env import (
    fetch_env_from_os,
    FETCH_ENV_FROM_OS_ERROR,
)


def test_fetch_env_from_os_returns_value_when_set():
    # given
    env_name = "TEST_ENV"
    env_value = "test_value"

    # when
    with patch.dict(os.environ, {env_name: env_value}):
        result = fetch_env_from_os(env_name)

    # then
    assert result == env_value


def test_fetch_env_from_os_raises_error_when_not_set():
    # given
    env_name = "TEST_ENV"

    # when
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(Exception) as excinfo:
            fetch_env_from_os(env_name)

    # then
    expect_msg = FETCH_ENV_FROM_OS_ERROR.format(env_name=env_name)
    assert expect_msg in str(excinfo.value)
