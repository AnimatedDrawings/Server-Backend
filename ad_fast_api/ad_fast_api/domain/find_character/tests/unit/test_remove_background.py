from ad_fast_api.domain.find_character.sources.features import (
    find_character_feature as fcf,
)
import numpy as np
from ad_fast_api.snippets.testings.ad_test.mock_ad_numpy import (
    sample_image_100x100_rgb,
    sample_image_100x100_white_background_rgb,
)


def test_remove_background(
    sample_image_100x100_rgb,
    sample_image_100x100_white_background_rgb,
):
    # given
    cropped_image = sample_image_100x100_rgb
    mask_image = sample_image_100x100_white_background_rgb
    # mask_image 중앙 부분(25:75, 25:75)을 255(흰색)로 설정
    # 50x50 크기의 중앙 사각형 영역을 마스크로 지정
    mask_image[25:75, 25:75] = 255

    # When
    result = fcf.remove_background(
        cropped_image=cropped_image,
        mask_image=mask_image,
    )

    # Then
    assert result.shape[-1] == 4  # 알파 채널을 포함한 BGRA 형식인지 검증
    assert isinstance(result, np.ndarray)  # 반환 타입이 올바른지(NumPy 배열) 확인
