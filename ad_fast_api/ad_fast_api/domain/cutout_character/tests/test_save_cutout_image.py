import pytest
import cv2
import numpy as np
import os
from fastapi import UploadFile
from io import BytesIO
from ad_fast_api.domain.cutout_character.sources.features import (
    save_cutout_image as sci,
)
from ad_fast_api.workspace.sources import conf_workspace as cw
from ad_fast_api.snippets.testings.mock_logger import mock_logger
from ad_fast_api.domain.cutout_character.sources.errors import (
    cutout_character_500_status as cc5s,
)
from unittest.mock import patch


##############################
# save_cutout_character_image_async 관련 테스트
##############################
@pytest.mark.asyncio
async def test_save_cutout_character_image_async(tmp_path):
    # given
    base_path = tmp_path
    mock_file = UploadFile(
        filename="test.png",
        file=BytesIO(b"Hello, Async World!"),
    )

    # when
    await sci.save_cutout_character_image_async(
        file=mock_file,
        base_path=base_path,
    )

    # then
    cutout_character_image_path = base_path.joinpath(cw.CUTOUT_CHARACTER_IMAGE_NAME)
    assert cutout_character_image_path.exists()


##############################
# rotate_cutout_image 관련 테스트
##############################
def test_missing_cropped_image(tmp_path, mock_logger):
    """
    cropped 이미지가 없는 경우: 예외 발생 확인
    """
    # cutout 이미지 파일만 생성
    cutout_path = tmp_path / cw.CUTOUT_CHARACTER_IMAGE_NAME
    dummy_image = np.ones((100, 100, 3), dtype=np.uint8) * 255
    cv2.imwrite(str(cutout_path), dummy_image)

    with pytest.raises(Exception) as excinfo:
        sci.resize_cutout_image(
            base_path=tmp_path,
            logger=mock_logger,
        )

    expected_msg = cc5s.NOT_FOUND_CROPPED_IMAGE.format(
        cropped_image_path=tmp_path / cw.CROPPED_IMAGE_NAME
    )
    assert expected_msg == str(excinfo.value)
    mock_logger.critical.assert_called_once_with(expected_msg)


def test_missing_cutout_image(tmp_path, mock_logger):
    """
    cutout 이미지가 없는 경우: 예외 발생 확인
    """
    # cropped 이미지 파일만 생성
    cropped_path = tmp_path / cw.CROPPED_IMAGE_NAME
    dummy_image = np.ones((100, 100, 3), dtype=np.uint8) * 127
    cv2.imwrite(str(cropped_path), dummy_image)

    with pytest.raises(Exception) as excinfo:
        sci.resize_cutout_image(
            base_path=tmp_path,
            logger=mock_logger,
        )

    expected_msg = cc5s.NOT_FOUND_CUTOUT_CHARACTER_IMAGE.format(
        cutout_character_image_path=tmp_path / cw.CUTOUT_CHARACTER_IMAGE_NAME
    )
    assert expected_msg == str(excinfo.value)
    mock_logger.critical.assert_called_once_with(expected_msg)


def test_same_size_no_resize(tmp_path, mock_logger):
    """
    cropped 이미지와 cutout 이미지의 크기가 동일하면,
    리사이즈를 수행하지 않아 파일이 변경되지 않아야 함.
    """
    cropped_path = tmp_path / cw.CROPPED_IMAGE_NAME
    cutout_path = tmp_path / cw.CUTOUT_CHARACTER_IMAGE_NAME

    image_shape = (100, 100, 3)
    cropped_image = np.ones(image_shape, dtype=np.uint8) * 200
    cutout_image = np.ones(image_shape, dtype=np.uint8) * 100

    cv2.imwrite(str(cropped_path), cropped_image)
    cv2.imwrite(str(cutout_path), cutout_image)

    mod_time_before = os.path.getmtime(cutout_path)
    _ = sci.resize_cutout_image(
        base_path=tmp_path,
        logger=mock_logger,
    )
    mod_time_after = os.path.getmtime(cutout_path)

    # 파일이 변경되지 않았음을 확인 (리사이즈가 수행되지 않음)
    assert mod_time_before == mod_time_after
    result_image = cv2.imread(str(cutout_path), cv2.IMREAD_UNCHANGED)
    assert result_image.shape == (100, 100, 3)


def test_resize_cutout_image_downscale(tmp_path, mock_logger):
    """
    cropped 이미지의 크기로 리사이즈(다운스케일)되는 경우를 확인
    cropped 이미지: (100, 100)
    cutout 이미지: (150, 150)
    """
    cropped_path = tmp_path / cw.CROPPED_IMAGE_NAME
    cutout_path = tmp_path / cw.CUTOUT_CHARACTER_IMAGE_NAME

    cropped_image = np.ones((100, 100, 3), dtype=np.uint8) * 150
    cutout_image = np.ones((150, 150, 3), dtype=np.uint8) * 100

    cv2.imwrite(str(cropped_path), cropped_image)
    cv2.imwrite(str(cutout_path), cutout_image)

    result = sci.resize_cutout_image(
        base_path=tmp_path,
        logger=mock_logger,
    )

    # resized 이미지의 크기가 cropped 이미지의 크기와 동일해야 함
    if result is None:
        raise Exception("result is None")
    (cropped_image, resized_cutout_image) = result
    assert resized_cutout_image is not None
    assert resized_cutout_image.shape[:2] == (100, 100)


def test_resize_cutout_image_upscale(tmp_path, mock_logger):
    """
    cropped 이미지의 크기로 리사이즈(업스케일)되는 경우를 확인
    cropped 이미지: (150, 150)
    cutout 이미지: (100, 100)
    """
    cropped_path = tmp_path / cw.CROPPED_IMAGE_NAME
    cutout_path = tmp_path / cw.CUTOUT_CHARACTER_IMAGE_NAME

    cropped_image = np.ones((150, 150, 3), dtype=np.uint8) * 150
    cutout_image = np.ones((100, 100, 3), dtype=np.uint8) * 50

    cv2.imwrite(str(cropped_path), cropped_image)
    cv2.imwrite(str(cutout_path), cutout_image)

    result = sci.resize_cutout_image(
        base_path=tmp_path,
        logger=mock_logger,
    )

    if result is None:
        raise Exception("result is None")
    (cropped_image, resized_cutout_image) = result
    assert resized_cutout_image is not None
    assert resized_cutout_image.shape[:2] == (150, 150)


def test_failed_write_cutout_image(monkeypatch, tmp_path, mock_logger):
    """
    resized 작업 후 cv2.imwrite 실패 시 FAILED_TO_WRITE_CUTOUT_IMAGE 예외가 발생하는지 테스트
    """
    # given
    cropped_path = tmp_path / cw.CROPPED_IMAGE_NAME
    cutout_path = tmp_path / cw.CUTOUT_CHARACTER_IMAGE_NAME
    # cropped 이미지와 cutout 이미지를 각각 생성
    # cropped: 100x100, cutout: 150x150 (resize가 수행되도록 함)
    cropped_image = np.ones((100, 100, 3), dtype=np.uint8) * 150
    cutout_image = np.ones((150, 150, 3), dtype=np.uint8) * 100
    cv2.imwrite(str(cropped_path), cropped_image)
    cv2.imwrite(str(cutout_path), cutout_image)

    # when
    with patch("cv2.imwrite", return_value=False):
        with pytest.raises(Exception) as excinfo:
            sci.resize_cutout_image(base_path=tmp_path, logger=mock_logger)

    # then
    expected_msg = cc5s.FAILED_TO_WRITE_CUTOUT_IMAGE.format(
        cutout_image_path=cutout_path
    )
    assert expected_msg in str(excinfo.value)
    mock_logger.critical.assert_called_once_with(expected_msg)


##############################
# recreate_mask_image 관련 테스트
##############################
def test_recreate_mask_image_without_alpha(tmp_path, mock_logger):
    """
    테스트: cutout 이미지에 알파 채널이 없는 경우
    -> cc5s.CUTOUT_CHARACTER_IMAGE_DOES_NOT_HAVE_ALPHA_CHANNEL 예외가 발생해야 함.
    """
    # 3채널 이미지 생성 (알파 채널 없음)
    cutout_image = np.zeros((50, 50, 3), dtype=np.uint8)

    with pytest.raises(Exception) as excinfo:
        sci.recreate_mask_image(
            cutout_image=cutout_image, base_path=tmp_path, logger=mock_logger
        )

    expected_msg = cc5s.CUTOUT_CHARACTER_IMAGE_DOES_NOT_HAVE_ALPHA_CHANNEL
    assert expected_msg in str(excinfo.value)
    mock_logger.critical.assert_called_once_with(expected_msg)


def test_recreate_mask_image_write_failure(monkeypatch, tmp_path, mock_logger):
    """
    테스트: 마스크 이미지 저장 실패 케이스
    -> cv2.imwrite가 실패하여 FAILED_TO_WRITE_MASK_IMAGE 예외가 발생해야 함.
    """
    # 4채널 이미지 생성 (알파 채널을 포함)
    cutout_image = np.zeros((50, 50, 4), dtype=np.uint8)
    cutout_image[:, :, 3] = 100  # 임의의 알파값 설정

    # cv2.imwrite가 항상 False를 반환하도록 monkeypatch 적용
    monkeypatch.setattr(cv2, "imwrite", lambda path, img, *args, **kwargs: False)

    with pytest.raises(Exception) as excinfo:
        sci.recreate_mask_image(
            cutout_image=cutout_image, base_path=tmp_path, logger=mock_logger
        )

    mask_image_path = tmp_path / cw.MASK_IMAGE_NAME
    expected_msg = cc5s.FAILED_TO_WRITE_MASK_IMAGE.format(
        mask_image_path=mask_image_path
    )
    assert expected_msg in str(excinfo.value)
    mock_logger.critical.assert_called_once_with(expected_msg)


def test_recreate_mask_image_success(tmp_path, mock_logger):
    """
    테스트: 정상적인 cutout 이미지로부터 mask 이미지 생성 성공
    -> mask 이미지가 생성되고, 읽은 이미지가 단일 채널이며 내용이 올바른지 확인.
    """
    # 4채널 이미지 생성 (알파 채널 포함)
    cutout_image = np.zeros((50, 50, 4), dtype=np.uint8)
    cutout_alpha_value = 150
    cutout_image[:, :, 3] = cutout_alpha_value

    sci.recreate_mask_image(
        cutout_image=cutout_image, base_path=tmp_path, logger=mock_logger
    )

    mask_image_path = tmp_path / cw.MASK_IMAGE_NAME
    assert mask_image_path.exists()

    # 저장된 마스크 이미지 읽기 (단일 채널로 저장됨)
    mask_image = cv2.imread(str(mask_image_path), cv2.IMREAD_UNCHANGED)
    assert mask_image is not None, "Mask image를 읽을 수 없습니다."
    assert mask_image.ndim == 2, "마스크 이미지는 단일 채널이어야 합니다."
    assert (
        mask_image == cutout_alpha_value
    ).all(), "저장된 마스크 이미지의 값이 예상과 다릅니다."
