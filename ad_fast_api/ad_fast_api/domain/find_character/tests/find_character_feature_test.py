from pathlib import Path
import cv2
import numpy as np
from ad_fast_api.domain.find_character.sources.find_character_feature import crop_image
from ad_fast_api.domain.schema.sources.schemas import BoundingBox
from ad_fast_api.workspace.sources import conf_workspace as cw
from ad_fast_api.snippets.sources.ad_test import measure_execution_time


def test_crop_image_async(tmp_path: Path):
    # 테스트용 이미지 생성
    original_img = np.ones((100, 100, 3), dtype=np.uint8) * 255  # 흰색 배경
    original_img[20:50, 10:30] = 0  # 검정색 사각형 영역 추가
    origin_path = tmp_path / cw.ORIGIN_IMAGE_NAME
    cv2.imwrite(str(origin_path), original_img)

    # 테스트용 bounding box 설정
    bbox = BoundingBox(left=10, right=30, top=20, bottom=50)

    # 실행 시간 측정
    measure_execution_time("crop_image")(crop_image)(
        base_path=tmp_path, bounding_box=bbox
    )

    # 결과 검증
    cropped_path = tmp_path / cw.CROPPED_IMAGE_NAME
    assert cropped_path.exists()

    cropped_img = cv2.imread(str(cropped_path))
    assert cropped_img.shape == (30, 20, 3)  # 높이 30, 너비 20 확인
    assert np.all(cropped_img == 0)  # 모든 픽셀이 검정색인지 확인
