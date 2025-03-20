import cv2
import numpy as np
from ad_fast_api.domain.find_character.sources.features import (
    find_character_feature as fcf,
)
from ad_fast_api.snippets.testings.ad_test.ad_test_helper import measure_execution_time
from ad_fast_api.domain.schema.sources.schemas import BoundingBox
from ad_fast_api.workspace.sources import conf_workspace as cw
from ad_fast_api.snippets.testings.ad_test.mock_ad_numpy import (
    sample_image_10MB_white_background_rgb,
)


def test_crop_image(sample_image_10MB_white_background_rgb, tmp_path):
    # 테스트용 이미지 생성 (약 10MB 크기)
    original_img = sample_image_10MB_white_background_rgb
    original_img[20:50, 10:30] = 0  # 검정색 사각형 영역 추가

    # 이미지 크기 출력
    image_size_bytes = original_img.nbytes
    image_size_mb = image_size_bytes / (1024 * 1024)
    print(f"Image size: {image_size_bytes:,} bytes ({image_size_mb:.2f} MB)")

    origin_path = tmp_path / cw.ORIGIN_IMAGE_NAME
    cv2.imwrite(str(origin_path), original_img)

    # 테스트용 bounding box 설정
    bbox = BoundingBox(left=10, right=30, top=20, bottom=50)

    # 실행 시간 측정
    cropped_image = measure_execution_time("crop_image")(fcf.crop_image)(
        base_path=tmp_path, bounding_box=bbox
    )

    # 결과 검증
    # 높이 30, 너비 20 확인
    assert cropped_image.shape == (30, 20, 3)  # type: ignore
    # 모든 픽셀이 검정색인지 확인
    assert np.all(cropped_image == 0)
