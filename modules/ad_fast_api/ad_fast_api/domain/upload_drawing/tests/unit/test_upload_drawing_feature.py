import pytest
from fastapi import UploadFile, HTTPException
from io import BytesIO
from ad_fast_api.domain.upload_drawing.sources.features import (
    upload_drawing_feature as udf,
)
from ad_fast_api.domain.upload_drawing.testings import (
    fake_upload_drawing as fud,
)
from ad_fast_api.domain.upload_drawing.sources.errors import (
    upload_drawing_400_status as ud4s,
)
from unittest.mock import patch, Mock, AsyncMock
from ad_fast_api.domain.schema.sources.schemas import BoundingBox
from ad_fast_api.workspace.sources.conf_workspace import BOUNDING_BOX_FILE_NAME


@pytest.mark.asyncio
async def test_save_origin_image_success():
    # given
    ad_id = "1234567890_hexcode"
    with (
        patch.object(
            udf,
            "get_file_bytes",
            return_value=b"Hello, Async World!",
        ),
        patch.object(
            udf,
            "make_ad_id",
            return_value=ad_id,
        ),
        patch.object(
            udf,
            "create_base_dir",
            return_value=fud.fake_workspace_files_path.joinpath(ad_id),
        ),
        patch.object(
            udf,
            "save_image_async",
            return_value=ad_id,
        ),
    ):
        # when
        expect_ad_id = await udf.save_origin_image_async(
            file=UploadFile(
                filename="test.png",
                file=BytesIO(b"Hello, Async World!"),
            )
        )
        # then
        assert expect_ad_id == ad_id


@pytest.mark.asyncio
async def test_save_origin_image_fail_file_bytes_is_empty():
    # given
    ad_id = "1234567890_hexcode"
    with (
        patch.object(
            udf,
            "make_ad_id",
            return_value=ad_id,
        ),
        patch.object(
            udf,
            "create_base_dir",
            return_value=fud.fake_workspace_files_path.joinpath(ad_id),
        ),
        patch.object(
            udf,
            "get_file_bytes",
            return_value=None,
        ),
        patch.object(
            udf,
            "save_image_async",
            side_effect=ud4s.UPLOADED_FILE_EMPTY_OR_INVALID,
        ),
    ):
        # when
        with pytest.raises(HTTPException) as exc_info:
            await udf.save_origin_image_async(
                file=UploadFile(
                    filename="test.png",
                    file=BytesIO(b"Hello, Async World!"),
                )
            )

        # then
        assert (
            exc_info.value.status_code
            == ud4s.UPLOADED_FILE_EMPTY_OR_INVALID.status_code
        )
        assert exc_info.value.detail == ud4s.UPLOADED_FILE_EMPTY_OR_INVALID.detail


@pytest.mark.asyncio
async def test_detect_character_success():
    # given
    ad_id = "test_ad_id"
    fake_base_path = fud.fake_workspace_files_path
    fake_logger = Mock()
    fake_img = "fake_image"  # check_image_is_rgb가 반환할 가짜 이미지 (string, numpy array 등 상관없음)
    fake_img_after_resize = "resized_image"  # resize_image 결과
    fake_response = Mock()  # send_to_torchserve가 반환할 응답 객체
    fake_detection_results = [
        "detection1",
        "detection2",
    ]  # check_detection_results 반환값
    fake_bounding_box = BoundingBox.mock()  # calculate_bounding_box 반환값

    # 내부 의존함수 모두 patch 처리
    with patch.object(
        udf, "get_base_path", return_value=fake_base_path
    ) as mock_get_base_path, patch.object(
        udf, "setup_logger", return_value=fake_logger
    ) as mock_setup_logger, patch.object(
        udf, "check_image_is_rgb", return_value=fake_img
    ) as mock_check_image, patch.object(
        udf, "resize_image", return_value=fake_img_after_resize
    ) as mock_resize, patch.object(
        udf,
        "detect_character_from_origin_async",
        new=AsyncMock(return_value=fake_response),
    ) as mock_send, patch.object(
        udf, "check_detection_results", return_value=fake_detection_results
    ) as mock_check_detections, patch.object(
        udf, "sort_detection_results"
    ) as mock_sort, patch.object(
        udf, "calculate_bounding_box", return_value=fake_bounding_box
    ) as mock_calc, patch.object(
        udf, "dict_to_file", new=Mock()
    ) as mock_save:

        # when
        await udf.detect_character(ad_id)

    # then: 함수들이 올바른 인자와 순서로 호출되었는지 확인
    mock_get_base_path.assert_called_once_with(ad_id=ad_id)
    mock_setup_logger.assert_called_once_with(ad_id=ad_id)
    mock_check_image.assert_called_once_with(
        base_path=fake_base_path, logger=fake_logger
    )
    mock_resize.assert_called_once_with(img=fake_img)
    mock_send.assert_awaited_once_with(img=fake_img_after_resize, logger=fake_logger)
    mock_check_detections.assert_called_once_with(
        resp=fake_response, logger=fake_logger
    )
    mock_sort.assert_called_once_with(
        detection_results=fake_detection_results, logger=fake_logger
    )
    mock_calc.assert_called_once_with(
        detection_results=fake_detection_results, logger=fake_logger
    )
    mock_save.assert_called_once_with(
        to_save_dict=fake_bounding_box.model_dump(mode="json"),
        file_path=fake_base_path.joinpath(BOUNDING_BOX_FILE_NAME),
    )


@pytest.mark.asyncio
async def test_detect_character_fail_image_is_not_rgb():
    # given
    ad_id = "test_ad_id"
    fake_base_path = fud.fake_workspace_files_path
    fake_logger = Mock()
    fake_img_after_resize = "resized_image"  # resize_image 결과
    fake_response = Mock()  # send_to_torchserve가 반환할 응답 객체
    fake_detection_results = [
        "detection1",
        "detection2",
    ]  # check_detection_results 반환값
    fake_bounding_box = BoundingBox.mock()  # calculate_bounding_box 반환값

    # 내부 의존함수 모두 patch 처리
    with patch.object(
        udf, "get_base_path", return_value=fake_base_path
    ) as mock_get_base_path, patch.object(
        udf, "setup_logger", return_value=fake_logger
    ) as mock_setup_logger, patch.object(
        udf, "check_image_is_rgb", side_effect=Exception("Image is not RGB")
    ) as mock_check_image, patch.object(
        udf, "resize_image", return_value=fake_img_after_resize
    ) as mock_resize, patch.object(
        udf,
        "detect_character_from_origin_async",
        new=AsyncMock(return_value=fake_response),
    ) as mock_send, patch.object(
        udf, "check_detection_results", return_value=fake_detection_results
    ) as mock_check_detections, patch.object(
        udf, "sort_detection_results"
    ) as mock_sort, patch.object(
        udf, "calculate_bounding_box", return_value=fake_bounding_box
    ) as mock_calc, patch.object(
        udf, "dict_to_file", new=Mock()
    ) as mock_save:

        # when
        try:
            await udf.detect_character(ad_id)
        except HTTPException as e:
            assert e.status_code == ud4s.IMAGE_IS_NOT_RGB.status_code
            assert e.detail == ud4s.IMAGE_IS_NOT_RGB.detail
