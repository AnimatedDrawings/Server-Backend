from ad_fast_api.domain.find_character.sources.features import (
    find_character_feature as fcf,
)
from ad_fast_api.snippets.testings.ad_test.mock_ad_numpy import (
    sample_image_100x100_rgb,
)
from ad_fast_api.workspace.sources import conf_workspace as cw
from ad_fast_api.domain.schema.sources.schemas import BoundingBox
from unittest.mock import patch, Mock
from ad_fast_api.snippets.testings.mock_logger import mock_logger
import numpy as np


def test_cv2_save_image(sample_image_100x100_rgb, tmp_path):
    image_name = "test.png"
    fcf.cv2_save_image(sample_image_100x100_rgb, image_name, tmp_path)
    assert tmp_path.joinpath(image_name).exists()


def test_save_bounding_box(tmp_path):
    """
    save_bounding_box 함수가 dict_to_file 함수를 올바른 파라미터로 호출하는지 확인
    """
    bounding_box = BoundingBox.mock()
    base_path = tmp_path

    with patch.object(
        fcf,
        "dict_to_file",
        new=Mock(),
    ) as mock_dict_to_file:
        fcf.save_bounding_box(
            bounding_box=bounding_box,
            base_path=base_path,
        )

    to_save_dict = bounding_box.model_dump(mode="json")
    file_path = base_path.joinpath(cw.BOUNDING_BOX_FILE_NAME)
    mock_dict_to_file.assert_called_once_with(
        to_save_dict=to_save_dict,
        file_path=file_path,
    )


def test_crop_and_segment_character_with_patch_object(tmp_path, mock_logger):
    ad_id = "test_ad_id"
    bounding_box = BoundingBox.mock()
    base_path = tmp_path  # 임시 경로 사용

    # 더미 이미지 생성
    cropped_image = np.full((100, 100, 3), 255, dtype=np.uint8)
    mask_image = np.full((100, 100), 127, dtype=np.uint8)
    removed_bg_image = np.full((100, 100, 3), 200, dtype=np.uint8)

    # 의존 함수들을 patch.object 로 대체
    with patch.object(
        fcf, "crop_image", return_value=cropped_image
    ) as mock_crop_image, patch.object(
        fcf, "cv2_save_image"
    ) as mock_cv2_save_image, patch.object(
        fcf, "segment_character", return_value=mask_image
    ) as mock_segment_character, patch.object(
        fcf, "remove_background", return_value=removed_bg_image
    ) as mock_remove_background, patch.object(
        fcf.cw, "get_base_path", return_value=base_path
    ) as mock_get_base_path:

        # 함수를 실행
        fcf.crop_and_segment_character(
            ad_id=ad_id,
            bounding_box=bounding_box,
            logger=mock_logger,
            base_path=base_path,  # base_path 가 전달되면 cw.get_base_path 는 사용되지 않습니다.
        )

        # cv2_save_image 가 세 번 호출되었는지 검증
        calls = mock_cv2_save_image.call_args_list
        assert len(calls) == 3, "cv2_save_image 함수는 세 번 호출되어야 합니다."

        # 첫 번째 호출: cropped_image, CROPPED_IMAGE_NAME, base_path
        args, kwargs = calls[0]
        assert kwargs["image"] is cropped_image
        assert kwargs["image_name"] == fcf.cw.CROPPED_IMAGE_NAME
        assert kwargs["base_path"] == base_path

        # 두 번째 호출: mask_image, MASK_IMAGE_NAME, base_path
        args, kwargs = calls[1]
        assert kwargs["image"] is mask_image
        assert kwargs["image_name"] == fcf.cw.MASK_IMAGE_NAME
        assert kwargs["base_path"] == base_path

        # 세 번째 호출: removed_bg_image, CUTOUT_CHARACTER_IMAGE_NAME, base_path
        args, kwargs = calls[2]
        assert kwargs["image"] is removed_bg_image
        assert kwargs["image_name"] == fcf.cw.CUTOUT_CHARACTER_IMAGE_NAME
        assert kwargs["base_path"] == base_path

        # crop_image, segment_character, remove_background
        # 올바른 인자와 함께 한 번 호출되었는지 검증
        mock_crop_image.assert_called_once_with(
            base_path=base_path,
            bounding_box=bounding_box,
        )

        mock_segment_character.assert_called_once_with(
            img=cropped_image,
            logger=mock_logger,
        )
        mock_remove_background.assert_called_once_with(
            cropped_image=cropped_image,
            mask_image=mask_image,
        )
