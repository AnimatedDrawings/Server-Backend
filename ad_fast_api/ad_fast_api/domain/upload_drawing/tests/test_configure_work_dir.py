from fastapi import UploadFile
from io import BytesIO
from ad_fast_api.domain.upload_drawing.sources.features import configure_work_dir as cwd
from ad_fast_api.snippets.testings import mock_ad_time
from ad_fast_api.domain.upload_drawing.testings import (
    fake_upload_drawing as fud,
)
from ad_fast_api.snippets.sources import save_image as si


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
    expect_file_bytes = si.get_file_bytes(file=file)

    # then
    assert expect_file_bytes == file_bytes
