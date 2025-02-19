import pytest
import json
import httpx
import respx
import numpy as np
from ad_fast_api.domain.upload_drawing.tests.conftest import TEST_DIR
from unittest.mock import patch, Mock, AsyncMock
from ad_fast_api.domain.upload_drawing.sources.features import detect_character as dc
from ad_fast_api.snippets.testings.mock_logger import mock_logger

from pathlib import Path


def test_check_image_is_rgb_success():
    # given
    mock_logger = Mock()
    origin_image_name = "test.png"

    # Mock cv2.imread to return a numpy array with correct shape (3D array)
    mock_image = np.zeros((2, 2, 3), dtype=np.uint8)  # 2x2 RGB image

    with patch("cv2.imread", return_value=mock_image):
        # when
        img = dc.check_image_is_rgb(
            base_path=TEST_DIR,
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
                base_path=TEST_DIR,
                logger=mock_logger,
                origin_image_name=origin_image_name,
            )
            # then
            expected_msg = dc.IMAGE_SHAPE_ERROR.format(len_shape=2)
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
async def test_send_to_torchserve_success(mock_logger):
    # given
    mock_response = httpx.Response(200, content=b'{"result": "success"}')
    route = respx.post(dc.TORCHSERVE_URL).mock(return_value=mock_response)

    # when
    test_img = np.zeros((224, 224, 3), dtype=np.uint8)
    response = await dc.send_to_torchserve(test_img, mock_logger)

    # then
    assert response.status_code == mock_response.status_code
    assert response.json() == mock_response.json()
    assert route.called
    mock_logger.critical.assert_not_called()


@pytest.mark.asyncio
@respx.mock
async def test_send_to_torchserve_fail_status_code_300(mock_logger):
    # given
    mock_response = httpx.Response(300, content=b"Bad Request")
    respx.post(dc.TORCHSERVE_URL).mock(return_value=mock_response)
    test_img = np.zeros((224, 224, 3), dtype=np.uint8)

    # when
    with pytest.raises(Exception) as exc_info:
        await dc.send_to_torchserve(test_img, mock_logger)

    # then
    expected_msg = dc.SEND_TO_TORCHSERVE_ERROR.format(resp=mock_response)
    assert str(exc_info.value) == expected_msg
    mock_logger.critical.assert_called_once_with(expected_msg)


@pytest.mark.asyncio
@respx.mock
async def test_send_to_torchserve_fail_connection_error(mock_logger):
    # given
    test_exception = httpx.ConnectError("Connection failed")
    respx.post(dc.TORCHSERVE_URL).mock(side_effect=test_exception)
    test_img = np.zeros((224, 224, 3), dtype=np.uint8)

    # when
    with pytest.raises(Exception) as exc_info:
        await dc.send_to_torchserve(test_img, mock_logger)

    # then
    expected_msg = dc.SEND_TO_TORCHSERVE_ERROR.format(resp=str(test_exception))
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
    expected_msg = dc.DETECTION_ERROR.format(detection_results=error_response)
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
    expected_msg = dc.REPORT_HIGHEST_SCORE_DETECTION.format(
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
    expected_msg = dc.NO_DETECTION_ERROR
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
    expected_msg = dc.REPORT_HIGHEST_SCORE_DETECTION.format(
        count=1,
        score=0.8,
    )
    mock_logger.info.assert_called_once_with(expected_msg)


def test_calculate_bounding_box_success(mock_logger):
    # given
    detection_results = [{"bbox": [10.6, 20.3, 30.7, 40.2], "score": 0.9}]
    expected_bbox = {"left": 11, "top": 20, "right": 31, "bottom": 40}

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
    expected_msg = dc.CALCULATE_BOUNDING_BOX_ERROR.format(error=key)
    assert expected_msg == str(exc_info.value)
    mock_logger.critical.assert_called_once_with(expected_msg)


@pytest.mark.asyncio
async def test_save_bounding_box_success():
    # given
    bounding_box = {"left": 11, "top": 20, "right": 31, "bottom": 40}
    base_path = TEST_DIR
    expected_path = base_path.joinpath(dc.BOUNDING_BOX_FILE_NAME)
    mock_file = AsyncMock()
    mock_file.__aenter__.return_value = mock_file
    dumped_yaml = "mocked_yaml_data"

    # when
    with patch(
        "aiofiles.open",
        return_value=mock_file,
    ) as mock_open, patch(
        "yaml.dump",
        return_value=dumped_yaml,
    ) as mock_dump:
        await dc.save_bounding_box(bounding_box, base_path)

        # then
        # 올바른 경로에 파일 생성 시도
        # YAML 직렬화가 올바른 데이터로 수행
        # 비동기 쓰기 작업이 정상적으로 호출
        mock_open.assert_called_once_with(expected_path.as_posix(), "w")
        mock_dump.assert_called_once_with(bounding_box)
        mock_file.write.assert_awaited_once_with(dumped_yaml)
