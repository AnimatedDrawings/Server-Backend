import numpy as np
import pytest


TEN_MB_SIZE = 1870


@pytest.fixture
def sample_image_100x100_rgb():
    # 테스트용 이미지 생성 (100x100 크기의 RGB 이미지)
    return np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)


@pytest.fixture
def sample_image_100x100_white_background_rgb():
    # 테스트용 마스크 생성 (100x100 크기의 이진 이미지)
    mask = np.zeros((100, 100), dtype=np.uint8)
    mask[25:75, 25:75] = 255  # 중앙에 흰색 사각형
    return mask


@pytest.fixture
def sample_image_10MB_rgb():
    # 테스트용 이미지 생성 (10MB 크기의 RGB 이미지)
    original_image = (
        np.random.randint(0, 255, (TEN_MB_SIZE, TEN_MB_SIZE, 3), dtype=np.uint8) * 255
    )
    return original_image


@pytest.fixture
def sample_image_10MB_white_background_rgb():
    # 테스트용 이미지 생성 (10MB 크기의 RGB 이미지, 흰색 배경)
    original_image = np.ones((TEN_MB_SIZE, TEN_MB_SIZE, 3), dtype=np.uint8) * 255
    return original_image
