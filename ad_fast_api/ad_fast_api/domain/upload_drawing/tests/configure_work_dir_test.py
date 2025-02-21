import pytest
from fastapi import UploadFile, HTTPException
from io import BytesIO
from pathlib import Path
from ad_fast_api.domain.upload_drawing.sources.features import configure_work_dir as cwd
from ad_fast_api.snippets.testings import mock_ad_time
from ad_fast_api.domain.upload_drawing.testings import (
    mock_configure_work_dir as mudf,
    fake_upload_drawing as fud,
)
from ad_fast_api.domain.upload_drawing.sources.helpers import (
    upload_drawing_http_exception as ude,
)
from ad_fast_api.workspace.sources import conf_workspace as cw
from ad_fast_api.snippets.sources.ad_test import measure_execution_time
from faker import Faker


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
        files_path=fud.fake_workspace_files_path,
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
async def test_save_origin_image_async(tmp_path: Path):
    # given
    base_path = fud.fake_workspace_files_path
    origin_image_path = base_path.joinpath(cw.ORIGIN_IMAGE_NAME)
    fake = Faker()
    file_bytes = fake.binary(length=10 * 1024 * 1024)

    # when
    await measure_execution_time("save_origin_image")(cwd.save_origin_image_async)(
        base_path=base_path,
        file_bytes=file_bytes,
    )

    # then
    assert origin_image_path.exists()
    assert origin_image_path.read_bytes() == file_bytes


@pytest.mark.asyncio
async def test_save_image_success():
    # given
    ad_id = "1234567890_hexcode"
    with (
        mudf.patcher_make_ad_id(return_value=ad_id),
        mudf.patcher_create_base_dir(
            return_value=fud.fake_workspace_files_path.joinpath(ad_id)
        ),
        mudf.patcher_get_file_bytes(return_value=b"Hello, Async World!"),
        mudf.patcher_save_origin_image_async(return_value=None),
    ):
        # when
        expect_ad_id = await cwd.save_image(
            file=UploadFile(
                filename="test.png",
                file=BytesIO(b"Hello, Async World!"),
            )
        )
        # then
        assert expect_ad_id == ad_id


@pytest.mark.asyncio
async def test_save_image_fail_file_bytes_is_empty():
    # given
    ad_id = "1234567890_hexcode"
    with (
        mudf.patcher_make_ad_id(return_value=ad_id),
        mudf.patcher_create_base_dir(
            return_value=fud.fake_workspace_files_path.joinpath(ad_id)
        ),
        mudf.patcher_get_file_bytes(return_value=None),
        mudf.patcher_save_origin_image_async(return_value=None),
    ):
        # when/then
        with pytest.raises(HTTPException) as exc_info:
            await cwd.save_image(
                file=UploadFile(
                    filename="test.png",
                    file=BytesIO(b"Hello, Async World!"),
                )
            )
        # then
        assert (
            exc_info.value.status_code
            == ude.UPLOADED_FILE_EMPTY_OR_INVALID.status_code()
        )
        assert exc_info.value.detail == ude.UPLOADED_FILE_EMPTY_OR_INVALID.detail()
