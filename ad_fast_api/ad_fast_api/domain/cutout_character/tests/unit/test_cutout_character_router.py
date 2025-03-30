import io
from unittest.mock import AsyncMock, patch
from ad_fast_api.domain.cutout_character.sources import cutout_character_router
import numpy as np
from ad_fast_api.snippets.testings.mock_logger import mock_logger


def test_cutout_character_success(mock_client):
    # given
    ad_id = "test_ad"
    path = "/cutout_character"
    params = {"ad_id": ad_id}
    fake_test_file = io.BytesIO(b"fake image content")
    fake_upload_file = {"file": ("test.png", fake_test_file, "image/png")}
    fake_cropped_image = np.zeros((100, 100, 3), dtype=np.uint8)
    fake_char_cfg_dict = {"width": 100, "height": 200, "skeleton": []}

    # when
    with patch.object(
        cutout_character_router,
        "setup_logger",
        return_value=mock_logger,
    ), patch.object(
        cutout_character_router,
        "save_cutout_image_async",
        new=AsyncMock(
            return_value=fake_cropped_image,
        ),
    ) as mock_save_image, patch.object(
        cutout_character_router,
        "configure_skeleton_async",
        new=AsyncMock(return_value=fake_char_cfg_dict),
    ) as mock_configure:
        response = mock_client.post(
            path,
            params=params,
            files=fake_upload_file,
        )

    # then
    assert response.status_code == 200


def test_cutout_character_fail_status_code_500(mock_client):
    # given
    ad_id = "test_ad"
    path = "/cutout_character"
    params = {"ad_id": ad_id}
    fake_test_file = io.BytesIO(b"fake image content")
    fake_upload_file = {"file": ("test.png", fake_test_file, "image/png")}

    # when
    with patch.object(
        cutout_character_router,
        "setup_logger",
        return_value=mock_logger,
    ), patch.object(
        cutout_character_router,
        "save_cutout_image_async",
        new=AsyncMock(
            side_effect=Exception(),
        ),
    ) as mock_save_image, patch.object(
        cutout_character_router,
        "configure_skeleton_async",
        new=AsyncMock(return_value={}),
    ) as mock_configure:
        response = mock_client.post(
            path,
            params=params,
            files=fake_upload_file,
        )

    # then
    assert response.status_code == 500


def test_cutout_character_fail_status_code_501(mock_client):
    # given
    ad_id = "test_ad"
    path = "/cutout_character"
    params = {"ad_id": ad_id}
    fake_test_file = io.BytesIO(b"fake image content")
    fake_upload_file = {"file": ("test.png", fake_test_file, "image/png")}
    fake_cropped_image = np.zeros((100, 100, 3), dtype=np.uint8)

    # when
    with patch.object(
        cutout_character_router,
        "setup_logger",
        return_value=mock_logger,
    ), patch.object(
        cutout_character_router,
        "save_cutout_image_async",
        new=AsyncMock(
            return_value=fake_cropped_image,
        ),
    ) as mock_save_image, patch.object(
        cutout_character_router,
        "configure_skeleton_async",
        new=AsyncMock(
            side_effect=Exception(),
        ),
    ) as mock_configure:
        response = mock_client.post(
            path,
            params=params,
            files=fake_upload_file,
        )

    # then
    assert response.status_code == 501
