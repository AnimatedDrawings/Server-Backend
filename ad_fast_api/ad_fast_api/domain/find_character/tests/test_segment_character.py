import numpy as np
import pytest
import cv2
from ad_fast_api.domain.find_character.sources.features import (
    segment_character as sc,
)
from ad_fast_api.snippets.testings.mock_logger import mock_logger
from ad_fast_api.domain.find_character.sources.features import (
    find_character_feature as fcf,
)
from ad_fast_api.workspace.testings import mock_conf_workspace as mcw
from ad_fast_api.snippets.sources.ad_logger import setup_logger
from ad_fast_api.workspace.sources import conf_workspace as cw
from ad_fast_api.domain.find_character.sources.features import segment_character as sc
from ad_fast_api.domain.find_character.sources.errors import (
    find_character_500_status as fcs,
)


def test_apply_threshold():
    """
    흰색 배경에 검은 사각형을 그려 만든 이미지를 대상으로 임계값 처리를 수행하고,
    결과가 0과 255의 이진 이미지임을 확인합니다.
    """
    # 200×200 크기의 흰색 이미지 생성
    img = np.full((200, 200, 3), 255, dtype=np.uint8)
    # 검은 사각형 그리기 (사각형 내부는 (0,0,0))
    cv2.rectangle(img, (50, 50), (150, 150), (0, 0, 0), -1)

    binary_img = sc.apply_threshold(img)
    # 결과는 2차원 배열이어야 하며, 픽셀 값은 0 또는 255임
    assert binary_img.ndim == 2
    unique_values = np.unique(binary_img)
    for val in unique_values:
        assert val in [0, 255]


def test_apply_morphology():
    """
    이진 이미지에 대해 형태학적 변환을 적용하여 노이즈가 제거되고 객체 영역이 확장되는 효과를 확인합니다.
    """
    # 100×100 크기의 이미지 생성: 검은 배경 위에 흰색 사각형
    img = np.zeros((100, 100), dtype=np.uint8)
    cv2.rectangle(img, (20, 20), (80, 80), 255, -1)
    # 사각형 내부 일부 픽셀을 0으로 만들어 작은 구멍(노이즈) 추가
    img[40:45, 40:45] = 0

    morph_img = sc.apply_morphology(img)
    # 출력의 shape은 입력과 동일
    assert morph_img.shape == img.shape
    # 형태학적 변환 후 흰색(255)인 영역의 픽셀 수가 원본보다 커지거나 같아야 함(구멍이 메워졌을 것이므로)
    assert np.count_nonzero(morph_img) >= np.count_nonzero(img)


def test_apply_floodfill():
    """
    플러드 필을 적용한 결과, 이미지의 가장자리가 확실히 0(배경)임을 확인합니다.
    """
    # 100×100 크기의 이미지: 배경은 0, 내부에 흰색 사각형 생성
    img = np.zeros((100, 100), dtype=np.uint8)
    cv2.rectangle(img, (20, 20), (80, 80), 255, -1)

    flood_img = sc.apply_floodfill(img)
    # 이미지의 가장자리(상하좌우)는 반드시 0이어야 함
    assert np.all(flood_img[0, :] == 0)
    assert np.all(flood_img[-1, :] == 0)
    assert np.all(flood_img[:, 0] == 0)
    assert np.all(flood_img[:, -1] == 0)


def test_extract_largest_contour(mock_logger):
    """
    100×100 크기의 원(원형 객체)이 포함된 이미지를 통해 최대 컨투어가 추출되고,
    결과가 0과 255의 이진 이미지임을 확인합니다.
    """
    # 200×200 크기의 이미지에 원 그리기
    img = np.zeros((200, 200), dtype=np.uint8)
    cv2.circle(img, (100, 100), 50, (255,), -1)

    mask = sc.extract_largest_contour(img, mock_logger)
    # mask는 원래 이미지 크기와 동일하며 0 또는 255의 값만 가짐.
    assert mask.shape == img.shape
    unique_values = np.unique(mask)
    for val in unique_values:
        assert val in [0, 255]


def test_extract_largest_contour_no_contours(mock_logger):
    """
    컨투어가 없는 경우, extract_largest_contour 함수가 Exception을 발생시키는지 확인합니다.
    floodfill 결과로 모든 픽셀이 255인 경우, 생성되는 inverted mask는 모두 0이 되어
    skimage.measure.find_contours가 빈 리스트를 반환하게 됩니다.
    """
    # floodfill 결과 이미지를 모두 255로 채워서 전달
    im_floodfill = np.full((100, 100), 255, dtype=np.uint8)

    with pytest.raises(Exception) as excinfo:
        sc.extract_largest_contour(im_floodfill, mock_logger)
    assert fcs.FOUND_NO_CONTOURS_WITHIN_IMAGE in str(excinfo.value)


def test_segment_character(mock_logger):
    """
    전체 파이프라인(segment_character)을 테스트합니다.
    흰색 배경에 검은 색 글자('A')를 그려 만든 이미지에 대해 올바른 이진 마스크가 생성되는지 확인합니다.
    """
    # 300×300 크기의 흰색 컬러 이미지 생성
    img = np.full((300, 300, 3), 255, dtype=np.uint8)
    # OpenCV를 이용하여 큰 글자 'A'를 그리기 (좌측 하단에서 시작)
    cv2.putText(
        img, "A", (50, 250), cv2.FONT_HERSHEY_SIMPLEX, 5, (0, 0, 0), thickness=10
    )

    mask = sc.segment_character(img, mock_logger)
    # mask는 이미지의 높이×너비 (2차원)이며, 흰색(255)와 검정(0)만 포함해야 함
    assert mask is not None
    assert mask.shape == img.shape[:2]
    unique_values = np.unique(mask)
    for val in unique_values:
        assert val in [0, 255]

    # 추출된 마스크에 'A' 영역(255인 영역)이 존재해야 함
    assert np.count_nonzero(mask) > 0


def segment_character_garlic():
    logger = setup_logger(base_path=mcw.GARLIC_PATH)

    cropped_image_path = mcw.GARLIC_PATH.joinpath(cw.CROPPED_IMAGE_NAME)
    img = cv2.imread(cropped_image_path.as_posix())

    mask_image = sc.segment_character(
        img=img,
        logger=logger,
    )

    fcf.cv2_save_image(
        image=mask_image,
        image_name="test_" + cw.MASK_IMAGE_NAME,
        base_path=mcw.GARLIC_TEST_PATH,
    )


if __name__ == "__main__":
    segment_character_garlic()
