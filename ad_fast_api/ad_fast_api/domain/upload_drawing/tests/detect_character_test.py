from ad_fast_api.domain.upload_drawing.tests.conftest import TEST_DIR
import pytest
from unittest.mock import patch, Mock
import numpy as np
from ad_fast_api.domain.upload_drawing.sources.features import detect_character as dc
import json
from httpx import Response
from pathlib import Path
import yaml


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


def test_check_image_is_rgb_raises_exception():
    # given
    mock_logger = Mock()
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


def test_send_to_torchserve_success():
    # given
    mock_logger = Mock()
    test_image = np.zeros((100, 100, 3), dtype=np.uint8)
    mock_response = Mock()
    mock_response.status_code = 200
    mock_encoded = Mock()
    mock_encoded.tobytes.return_value = b"mock_bytes"

    # when
    with patch("httpx.post", return_value=mock_response):
        with patch("cv2.imencode", return_value=(True, mock_encoded)):
            # then
            # Should not raise any exception
            dc.send_to_torchserve(
                img=test_image,
                logger=mock_logger,
                url="http://test-url",
            )


def test_send_to_torchserve_failed_status_code():
    # given
    mock_logger = Mock()
    test_image = np.zeros((100, 100, 3), dtype=np.uint8)
    mock_response = Mock()
    mock_response.status_code = 400
    mock_encoded = Mock()
    mock_encoded.tobytes.return_value = b"mock_bytes"

    # when
    with patch("httpx.post", return_value=mock_response):
        with patch("cv2.imencode", return_value=(True, mock_encoded)):
            with pytest.raises(Exception) as exc_info:
                dc.send_to_torchserve(
                    img=test_image,
                    logger=mock_logger,
                    url="http://test-url",
                )

            # then
            expected_msg = dc.SEND_TO_TORCHSERVE_ERROR.format(resp=mock_response)
            assert expected_msg == str(exc_info.value)
            mock_logger.critical.assert_called_once_with(expected_msg)


def test_send_to_torchserve_failed_none_response():
    # given
    mock_logger = Mock()
    test_image = np.zeros((100, 100, 3), dtype=np.uint8)
    mock_encoded = Mock()
    mock_encoded.tobytes.return_value = b"mock_bytes"

    # when
    with patch("httpx.post", return_value=None):
        with patch("cv2.imencode", return_value=(True, mock_encoded)):
            with pytest.raises(Exception) as exc_info:
                dc.send_to_torchserve(
                    img=test_image,
                    logger=mock_logger,
                    url="http://test-url",
                )

            # then
            expected_msg = dc.SEND_TO_TORCHSERVE_ERROR.format(resp=None)
            assert expected_msg == str(exc_info.value)
            mock_logger.critical.assert_called_once_with(expected_msg)


def test_check_detection_results_success():
    # given
    mock_logger = Mock()
    expected_results = {"predictions": [{"bbox": [1, 2, 3, 4]}]}
    mock_response = Mock(spec=Response)
    mock_response.content = json.dumps(expected_results).encode()

    # when
    results = dc.check_detection_results(
        resp=mock_response,
        logger=mock_logger,
    )

    # then
    assert results == expected_results


def test_check_detection_results_failed():
    # given
    mock_logger = Mock()
    error_response = {"code": 404, "message": "Model not found"}
    mock_response = Mock(spec=Response)
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


def test_check_detection_results_with_non_404_code():
    # given
    mock_logger = Mock()
    response_data = {"code": 500, "message": "Internal server error"}
    mock_response = Mock(spec=Response)
    mock_response.content = json.dumps(response_data).encode()

    # when
    results = dc.check_detection_results(
        resp=mock_response,
        logger=mock_logger,
    )

    # then
    assert results == response_data


def test_sort_detection_results_success():
    # given
    mock_logger = Mock()
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


def test_sort_detection_results_empty_list():
    # given
    mock_logger = Mock()
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


def test_sort_detection_results_single_item():
    # given
    mock_logger = Mock()
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


def test_calculate_bounding_box_success():
    # given
    mock_logger = Mock()
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


def test_calculate_bounding_box_failed():
    # given
    mock_logger = Mock()
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


def test_save_bounding_box_success():
    # given
    bounding_box = {"left": 11, "top": 20, "right": 31, "bottom": 40}
    base_path = TEST_DIR

    # when
    dc.save_bounding_box(
        bounding_box=bounding_box,
        base_path=base_path,
    )

    # then
    bounding_box_path = base_path.joinpath(dc.BOUNDING_BOX_FILE_NAME)
    assert bounding_box_path.exists()

    # verify content
    with open(bounding_box_path, "r") as f:
        saved_bbox = yaml.safe_load(f)

    assert saved_bbox == bounding_box

    # teardown
    bounding_box_path.unlink()
