from logging import Logger
from ad_fast_api.domain.upload_drawing.tests.conftest import TEST_DIR
import pytest
from unittest.mock import patch, Mock
import numpy as np
from ad_fast_api.domain.upload_drawing.sources.features import detect_character as dc

# import pytest
# import numpy as np
# import cv2
# from unittest.mock import patch
# from ad_fast_api.domain.upload_drawing.sources.features.detect_character import resize_image


def test_check_image_is_rgb_success(mock_logger: Logger):
    # given
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
            assert dc.IMAGE_SHAPE_ERROR in str(excinfo.value)


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


def test_send_to_torchserve_success(mock_logger):
    # given
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


def test_send_to_torchserve_failed_status_code(mock_logger):
    # given
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
            assert dc.SEND_TO_TORCHSERVE_ERROR in str(exc_info.value)


def test_send_to_torchserve_failed_none_response(mock_logger):
    # given
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
            assert dc.SEND_TO_TORCHSERVE_ERROR in str(exc_info.value)
