import cv2
from ad_fast_api.domain.find_character.sources.features import (
    remove_background as rb,
)
from ad_fast_api.domain.find_character.sources.features import (
    find_character_feature as fcf,
)
from ad_fast_api.workspace.sources import conf_workspace as cw
from ad_fast_api.workspace.testings import mock_conf_workspace as mcw
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


def remove_background_garlic():
    cropped_image_path = mcw.GARLIC_PATH.joinpath(cw.CROPPED_IMAGE_NAME)
    cropped_image = cv2.imread(cropped_image_path.as_posix())

    mask_image_path = mcw.GARLIC_PATH.joinpath(cw.MASK_IMAGE_NAME)
    mask_image = cv2.imread(mask_image_path.as_posix())

    removed_bg_image = rb.remove_background(
        cropped_image=cropped_image,
        mask_image=mask_image,
    )

    fcf.cv2_save_image(
        image=removed_bg_image,
        image_name="test_" + cw.CUTOUT_CHARACTER_IMAGE_NAME,
        base_path=mcw.RESULT_GARLIC_PATH,
    )


if __name__ == "__main__":
    remove_background_garlic()
