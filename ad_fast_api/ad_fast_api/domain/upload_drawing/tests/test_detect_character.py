import pytest
import json
import httpx
import respx
import numpy as np
from fastapi import HTTPException
from ad_fast_api.domain.upload_drawing.testings import fake_upload_drawing as fud
from unittest.mock import patch, Mock, AsyncMock
from ad_fast_api.domain.upload_drawing.sources.features import detect_character as dc
from ad_fast_api.domain.upload_drawing.sources.helpers import (
    upload_drawing_strings as uds,
)
from ad_fast_api.domain.upload_drawing.sources.helpers import (
    upload_drawing_http_exception as ude,
)
from ad_fast_api.snippets.testings.mock_logger import mock_logger
from ad_fast_api.domain.schema.sources.schemas import BoundingBox


def test_check_image_is_rgb_success():
    # given
    mock_logger = Mock()
    origin_image_name = "test.png"

    # Mock cv2.imread to return a numpy array with correct shape (3D array)
    mock_image = np.zeros((2, 2, 3), dtype=np.uint8)  # 2x2 RGB image

    with patch("cv2.imread", return_value=mock_image):
        # when
        img = dc.check_image_is_rgb(
            base_path=fud.fake_workspace_files_path,
            logger=mock_logger,
            origin_image_name=origin_image_name,
        )

        # then
        assert img is not None
        assert img.shape == (2, 2, 3)  # Check the image dimensions
        assert isinstance(img, np.ndarray)


def test_check_image_is_rgb_raises_exception(mock_logger):
    # given
    origin_image_name = "test.png"

    with patch("cv2.imread", return_value=[[0, 0], [0, 0]]):
        # when
        with pytest.raises(Exception) as excinfo:
            dc.check_image_is_rgb(
                base_path=fud.fake_workspace_files_path,
                logger=mock_logger,
                origin_image_name=origin_image_name,
            )
            # then
            expected_msg = uds.IMAGE_SHAPE_ERROR.format(len_shape=2)
            assert expected_msg == str(excinfo.value)
            mock_logger.critical.assert_called_once_with(expected_msg)


def test_resize_image_when_larger_than_1000():
    # given
    # Create a test image with dimensions larger than 1000
    original_height, original_width = 1500, 2000
    test_image = np.zeros((original_height, original_width, 3), dtype=np.uint8)

    # when
    resized_img = dc.resize_image(test_image)

    # then
    assert np.max(resized_img.shape) == 1000
    # Check if aspect ratio is maintained
    expected_scale = 1000 / max(original_height, original_width)
    assert resized_img.shape[0] == round(original_height * expected_scale)
    assert resized_img.shape[1] == round(original_width * expected_scale)


def test_resize_image_when_smaller_than_1000():
    # given
    # Create a test image with dimensions smaller than 1000
    original_height, original_width = 800, 600
    test_image = np.zeros((original_height, original_width, 3), dtype=np.uint8)

    # when
    resized_img = dc.resize_image(test_image)

    # then
    # Image should remain unchanged
    assert resized_img.shape == test_image.shape
    assert np.array_equal(resized_img, test_image)


@pytest.mark.asyncio
@respx.mock
async def test_send_to_torchserve_async_success(mock_logger):
    # given
    mock_response = httpx.Response(200, content=b'{"result": "success"}')
    route = respx.post(uds.TORCHSERVE_URL).mock(return_value=mock_response)

    # when
    test_img = np.zeros((224, 224, 3), dtype=np.uint8)
    response = await dc.send_to_torchserve_async(test_img, mock_logger)

    # then
    assert response.status_code == mock_response.status_code
    assert response.json() == mock_response.json()
    assert route.called
    mock_logger.critical.assert_not_called()


@pytest.mark.asyncio
@respx.mock
async def test_send_to_torchserve_async_fail_status_code_300(mock_logger):
    # given
    mock_response = httpx.Response(300, content=b"Bad Request")
    respx.post(uds.TORCHSERVE_URL).mock(return_value=mock_response)
    test_img = np.zeros((224, 224, 3), dtype=np.uint8)

    # when
    with pytest.raises(Exception) as exc_info:
        await dc.send_to_torchserve_async(test_img, mock_logger)

    # then
    expected_msg = uds.SEND_TO_TORCHSERVE_ERROR.format(resp=mock_response)
    assert str(exc_info.value) == expected_msg
    mock_logger.critical.assert_called_once_with(expected_msg)


@pytest.mark.asyncio
@respx.mock
async def test_send_to_torchserve_async_fail_connection_error(mock_logger):
    # given
    test_exception = httpx.ConnectError("Connection failed")
    respx.post(uds.TORCHSERVE_URL).mock(side_effect=test_exception)
    test_img = np.zeros((224, 224, 3), dtype=np.uint8)

    # when
    with pytest.raises(Exception) as exc_info:
        await dc.send_to_torchserve_async(test_img, mock_logger)

    # then
    expected_msg = uds.SEND_TO_TORCHSERVE_ERROR.format(resp=str(test_exception))
    assert str(exc_info.value) == expected_msg
    mock_logger.critical.assert_called_once_with(expected_msg)


def test_check_detection_results_success(mock_logger):
    # given
    expected_results = {"predictions": [{"bbox": [1, 2, 3, 4]}]}
    mock_response = Mock(spec=httpx.Response)
    mock_response.content = json.dumps(expected_results).encode()

    # when
    results = dc.check_detection_results(
        resp=mock_response,
        logger=mock_logger,
    )

    # then
    assert results == expected_results


def test_check_detection_results_failed(mock_logger):
    # given
    error_response = {"code": 404, "message": "Model not found"}
    mock_response = Mock(spec=httpx.Response)
    mock_response.content = json.dumps(error_response).encode()

    # when
    with pytest.raises(Exception) as exc_info:
        dc.check_detection_results(
            resp=mock_response,
            logger=mock_logger,
        )

    # then
    expected_msg = uds.DETECTION_ERROR.format(detection_results=error_response)
    assert expected_msg == str(exc_info.value)
    mock_logger.critical.assert_called_once_with(expected_msg)


def test_check_detection_results_with_non_404_code(mock_logger):
    # given
    response_data = {"code": 500, "message": "Internal server error"}
    mock_response = Mock(spec=httpx.Response)
    mock_response.content = json.dumps(response_data).encode()

    # when
    results = dc.check_detection_results(
        resp=mock_response,
        logger=mock_logger,
    )

    # then
    assert results == response_data


def test_sort_detection_results_success(mock_logger):
    # given
    detection_results = [
        {"score": 0.7, "bbox": [1, 2, 3, 4]},
        {"score": 0.9, "bbox": [5, 6, 7, 8]},
        {"score": 0.8, "bbox": [9, 10, 11, 12]},
    ]

    # when
    dc.sort_detection_results(
        detection_results=detection_results,
        logger=mock_logger,
    )

    # then
    assert detection_results[0]["score"] == 0.9  # Highest score first
    assert detection_results[1]["score"] == 0.8
    assert detection_results[2]["score"] == 0.7

    # Check if logger.info was called with correct message
    expected_msg = uds.REPORT_HIGHEST_SCORE_DETECTION.format(
        count=len(detection_results),
        score=detection_results[0]["score"],
    )
    mock_logger.info.assert_called_once_with(expected_msg)


def test_sort_detection_results_empty_list(mock_logger):
    # given
    detection_results = []

    # when
    with pytest.raises(Exception) as exc_info:
        dc.sort_detection_results(
            detection_results=detection_results,
            logger=mock_logger,
        )

    # then
    expected_msg = uds.NO_DETECTION_ERROR
    assert expected_msg == str(exc_info.value)
    mock_logger.critical.assert_called_once_with(expected_msg)


def test_sort_detection_results_single_item(mock_logger):
    # given
    detection_results = [
        {"score": 0.8, "bbox": [1, 2, 3, 4]},
    ]

    # when
    dc.sort_detection_results(
        detection_results=detection_results,
        logger=mock_logger,
    )

    # then
    assert detection_results[0]["score"] == 0.8

    # Check if logger.info was called with correct message
    expected_msg = uds.REPORT_HIGHEST_SCORE_DETECTION.format(
        count=1,
        score=0.8,
    )
    mock_logger.info.assert_called_once_with(expected_msg)


def test_calculate_bounding_box_success(mock_logger):
    # given
    l, t, r, b = 10.6, 20.3, 30.7, 40.2
    detection_results = [{"bbox": [l, t, r, b], "score": 0.9}]
    expected_bbox = BoundingBox(
        left=round(l),
        top=round(t),
        right=round(r),
        bottom=round(b),
    )

    # when
    result = dc.calculate_bounding_box(
        detection_results=detection_results,
        logger=mock_logger,
    )

    # then
    assert result == expected_bbox
    mock_logger.critical.assert_not_called()


def test_calculate_bounding_box_failed(mock_logger):
    # given
    detection_results = [{"invalid_key": "value"}]  # Missing bbox key

    # when
    with pytest.raises(Exception) as exc_info:
        dc.calculate_bounding_box(
            detection_results=detection_results,
            logger=mock_logger,
        )

    # then
    key = "'bbox'"
    expected_msg = uds.CALCULATE_BOUNDING_BOX_ERROR.format(error=key)
    assert expected_msg == str(exc_info.value)
    mock_logger.critical.assert_called_once_with(expected_msg)


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
    fake_bounding_box = {
        "left": 1,
        "top": 2,
        "right": 3,
        "bottom": 4,
    }  # calculate_bounding_box 반환값

    # 내부 의존함수 모두 patch 처리
    with patch.object(
        dc, "get_base_path", return_value=fake_base_path
    ) as mock_get_base_path, patch.object(
        dc, "setup_logger", return_value=fake_logger
    ) as mock_setup_logger, patch.object(
        dc, "check_image_is_rgb", return_value=fake_img
    ) as mock_check_image, patch.object(
        dc, "resize_image", return_value=fake_img_after_resize
    ) as mock_resize, patch.object(
        dc, "send_to_torchserve_async", new=AsyncMock(return_value=fake_response)
    ) as mock_send, patch.object(
        dc, "check_detection_results", return_value=fake_detection_results
    ) as mock_check_detections, patch.object(
        dc, "sort_detection_results"
    ) as mock_sort, patch.object(
        dc, "calculate_bounding_box", return_value=fake_bounding_box
    ) as mock_calc, patch.object(
        dc, "save_bounding_box", new=Mock()
    ) as mock_save:

        # when
        await dc.detect_character(ad_id)

    # then: 함수들이 올바른 인자와 순서로 호출되었는지 확인
    mock_get_base_path.assert_called_once_with(ad_id=ad_id)
    mock_setup_logger.assert_called_once_with(base_path=fake_base_path)
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
        bounding_box=fake_bounding_box, base_path=fake_base_path
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
    fake_bounding_box = {
        "left": 1,
        "top": 2,
        "right": 3,
        "bottom": 4,
    }  # calculate_bounding_box 반환값

    # 내부 의존함수 모두 patch 처리
    with patch.object(
        dc, "get_base_path", return_value=fake_base_path
    ) as mock_get_base_path, patch.object(
        dc, "setup_logger", return_value=fake_logger
    ) as mock_setup_logger, patch.object(
        dc, "check_image_is_rgb", side_effect=Exception("Image is not RGB")
    ) as mock_check_image, patch.object(
        dc, "resize_image", return_value=fake_img_after_resize
    ) as mock_resize, patch.object(
        dc, "send_to_torchserve_async", new=AsyncMock(return_value=fake_response)
    ) as mock_send, patch.object(
        dc, "check_detection_results", return_value=fake_detection_results
    ) as mock_check_detections, patch.object(
        dc, "sort_detection_results"
    ) as mock_sort, patch.object(
        dc, "calculate_bounding_box", return_value=fake_bounding_box
    ) as mock_calc, patch.object(
        dc, "save_bounding_box", new=Mock()
    ) as mock_save:

        # when
        try:
            await dc.detect_character(ad_id)
        except HTTPException as e:
            assert e.status_code == ude.IMAGE_IS_NOT_RGB.status_code()
            assert e.detail == ude.IMAGE_IS_NOT_RGB.detail()
