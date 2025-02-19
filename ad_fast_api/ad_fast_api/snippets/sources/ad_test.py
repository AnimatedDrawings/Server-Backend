from unittest.mock import AsyncMock, patch
import aiofiles
import pytest


@pytest.fixture(scope="function")
def mock_aiofiles_open_wirte():
    mock_file = AsyncMock()
    mock_file.write = AsyncMock()
    mock_aiofiles_open_aenter = AsyncMock(
        return_value=mock_file,
    )
    mock_aiofiles_open = AsyncMock(
        __aenter__=mock_aiofiles_open_aenter,
    )

    patcher = patch.object(
        aiofiles,
        "open",
        return_value=mock_aiofiles_open,
    )
    patcher.start()

    yield mock_file

    patcher.stop()


def patcher_aiofiles_open_wirte(
    return_value=None,
    side_effect=None,
):
    mock_file = AsyncMock()
    mock_file.write = AsyncMock(
        return_value=return_value,
        side_effect=side_effect,
    )
    mock_aiofiles_open_aenter = AsyncMock(
        return_value=mock_file,
    )
    mock_aiofiles_open = AsyncMock(
        __aenter__=mock_aiofiles_open_aenter,
    )

    patcher = patch.object(
        aiofiles,
        "open",
        return_value=mock_aiofiles_open,
    )
    return patcher
