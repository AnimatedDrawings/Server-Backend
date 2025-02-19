import pytest
from unittest.mock import patch, AsyncMock
from fastapi import UploadFile, HTTPException
from io import BytesIO
from ad_fast_api.domain.upload_drawing.sources.features import configure_work_dir as cwd
from ad_fast_api.snippets.testings import mock_ad_time
from pathlib import Path
from ad_fast_api.domain.upload_drawing.testings import (
    mock_upload_drawing_feature as mudf,
)
from ad_fast_api.domain.upload_drawing.tests.conftest import TEST_DIR


def test_make_ad_id():
    # given
    now = mock_ad_time.FIX_NOW
    uuid = "hexcode"

    # when
    ad_id = cwd.make_ad_id(
        now=now,
        uuid=uuid,
    )

    # then
    now_str = now.strftime("%Y%m%d%H%M%S")
    assert ad_id == now_str + "_" + "hexcode"


def test_create_base_dir():
    # given
    ad_id = "1234567890_hexcode"

    # when
    base_path = cwd.create_base_dir(
        ad_id=ad_id,
        files_path=TEST_DIR,
    )

    # then
    assert base_path.is_dir()

    # teardown
    base_path.rmdir()


def test_get_file_bytes():
    # given
    file_bytes = b"Hello, World!"
    file = UploadFile(
        filename="test.png",
        file=BytesIO(file_bytes),
    )

    # when
    expect_file_bytes = cwd.get_file_bytes(file=file)

    # then
    assert expect_file_bytes == file_bytes


@pytest.mark.asyncio
async def test_save_origin_image():
    # given
    base_path = TEST_DIR
    origin_image_path = base_path.joinpath(cwd.ORIGIN_IMAGE_NAME)
    file_bytes = b"Hello, Async World!"
    mock_file = AsyncMock()
    mock_file.__aenter__.return_value = mock_file

    # when
    with patch(
        "aiofiles.open",
        return_value=mock_file,
    ) as mock_open:
        await cwd.save_origin_image(
            base_path=base_path,
            file_bytes=file_bytes,
        )

        # then
        mock_open.assert_called_once_with(origin_image_path.as_posix(), "wb")
        mock_file.write.assert_awaited_once_with(file_bytes)


@pytest.mark.asyncio
async def test_save_image_success():
    # given
    ad_id = "1234567890_hexcode"
    patcher1 = mudf.patcher_make_ad_id(return_value=ad_id)
    patcher2 = mudf.patcher_create_base_dir(return_value=TEST_DIR.joinpath(ad_id))
    patcher3 = mudf.patcher_get_file_bytes(return_value=b"Hello, Async World!")
    patcher4 = mudf.patcher_save_origin_image(return_value=None)

    patcher1.start()
    patcher2.start()
    patcher3.start()
    patcher4.start()

    # when
    expect_ad_id = await cwd.save_image(
        file=UploadFile(
            filename="test.png",
            file=BytesIO(b"Hello, Async World!"),
        )
    )

    # then
    assert expect_ad_id == ad_id

    # teardown
    patcher1.stop()
    patcher2.stop()
    patcher3.stop()
    patcher4.stop()


@pytest.mark.asyncio
async def test_save_image_fail_file_bytes_is_empty():
    # given
    ad_id = "1234567890_hexcode"
    patcher1 = mudf.patcher_make_ad_id(return_value=ad_id)
    patcher2 = mudf.patcher_create_base_dir(return_value=TEST_DIR.joinpath(ad_id))
    patcher3 = mudf.patcher_get_file_bytes(return_value=None)
    patcher4 = mudf.patcher_save_origin_image(return_value=None)

    patcher1.start()
    patcher2.start()
    patcher3.start()
    patcher4.start()

    # when
    try:
        await cwd.save_image(
            file=UploadFile(
                filename="test.png",
                file=BytesIO(b"Hello, Async World!"),
            )
        )
    except HTTPException as e:
        assert e.status_code == 400
        assert e.detail == cwd.UPLOADED_FILE_EMPTY_OR_INVALID

    # teardown
    patcher1.stop()
    patcher2.stop()
    patcher3.stop()
    patcher4.stop()
