import cv2
import numpy as np
import pytest
from io import BytesIO
from fastapi import UploadFile
from ad_fast_api.domain.cutout_character.sources.features import (
    cutout_character_feature as ccf,
)
from ad_fast_api.workspace.sources import conf_workspace as cw
from ad_fast_api.snippets.testings.mock_logger import mock_logger


@pytest.mark.asyncio
async def test_save_cutout_image_success(tmp_path, mock_logger):
    """
    성공 케이스 테스트:
    - 임시 폴더에 cropped 이미지 (기준: 100x100, 3채널)를 미리 생성
    - 4채널 cutout 이미지를 파일 업로드 형식(UploadFile)으로 생성 (원본 크기 150x150)
    - save_cutout_image 호출 후, cutout 이미지가 cropped 이미지 크기로 리사이즈되고
      해당 이미지의 알파 채널을 mask 이미지로 추출하여 저장했음을 검증.
    """
    # 1. cropped 이미지 생성 (100x100, 3채널)
    cropped_img = np.full((100, 100, 3), 220, dtype=np.uint8)  # 예시: 밝은 회색 이미지
    cropped_path = tmp_path / cw.CROPPED_IMAGE_NAME
    cv2.imwrite(str(cropped_path), cropped_img)

    # 2. cutout 이미지 생성 (150x150, 4채널)
    # 알파 채널에 200 값을 채워 넣음 (나머지 채널은 임의 값)
    cutout_img = np.zeros((150, 150, 4), dtype=np.uint8)
    cutout_img[:, :, 0] = 50  # Blue 채널
    cutout_img[:, :, 1] = 100  # Green 채널
    cutout_img[:, :, 2] = 150  # Red 채널
    cutout_img[:, :, 3] = 200  # Alpha 채널 (mask로 사용)
    # PNG 형식으로 인코딩
    success, encoded_image = cv2.imencode(".png", cutout_img)
    assert success, "cutout 이미지를 PNG 형식으로 인코딩하는 데 실패했습니다."
    file_bytes = BytesIO(encoded_image.tobytes())
    upload_file = UploadFile(filename="test_cutout.png", file=file_bytes)

    # 3. save_cutout_image 함수 호출
    await ccf.save_cutout_image(
        file=upload_file, base_path=tmp_path, logger=mock_logger
    )

    # 4. 저장된 cutout 이미지 확인
    cutout_image_path = tmp_path / cw.CUTOUT_CHARACTER_IMAGE_NAME
    resized_cutout = cv2.imread(str(cutout_image_path), cv2.IMREAD_UNCHANGED)
    assert (
        resized_cutout is not None
    ), "Resized cutout 이미지 파일이 생성되지 않았습니다."
    # cropped 이미지 크기에 맞게 리사이즈되었는지 확인 (100x100)
    assert (
        resized_cutout.shape[0] == 100 and resized_cutout.shape[1] == 100
    ), f"리사이즈된 이미지 크기가 100x100이 아닙니다. 현재 크기: {resized_cutout.shape[:2]}"
    # 4채널 이미지임을 확인 (리사이즈 후에도 알파 채널이 유지되어야 함)
    assert (
        resized_cutout.shape[2] == 4
    ), "리사이즈된 cutout 이미지에 알파 채널이 없습니다."

    # 5. 생성된 mask 이미지 확인
    mask_image_path = tmp_path / cw.MASK_IMAGE_NAME
    mask_img = cv2.imread(str(mask_image_path), cv2.IMREAD_UNCHANGED)
    assert mask_image_path.exists(), "mask 이미지 파일이 생성되지 않았습니다."
    assert mask_img is not None, "mask 이미지를 읽을 수 없습니다."
    # mask 이미지는 단일 채널로 저장되어야 함
    assert (
        mask_img.ndim == 2
    ), f"mask 이미지의 채널 수가 1이 아닙니다. 현재 채널 수: {mask_img.ndim}"
    # 모든 픽셀 값이 리사이즈된 cutout 이미지의 알파 채널 값과 동일해야 함 (대부분의 보간법에서 균일한 값 유지)
    expected_alpha = 200
    # 보간 및 리사이즈 과정에서 미세한 오차가 있을 수 있으므로 np.allclose 사용
    assert np.allclose(
        mask_img, expected_alpha, atol=5
    ), "mask 이미지의 픽셀 값이 예상과 다릅니다."
