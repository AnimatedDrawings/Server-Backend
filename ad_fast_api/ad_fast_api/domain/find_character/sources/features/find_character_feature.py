import cv2
from pathlib import Path
from ad_fast_api.domain.schema.sources.schemas import BoundingBox
from ad_fast_api.workspace.sources import conf_workspace as cw
import numpy as np
from logging import Logger
from ad_fast_api.domain.find_character.sources.features.segment_character import (
    segment_character,
)
from ad_fast_api.domain.find_character.sources.features.crop_image import (
    crop_image,
)
from ad_fast_api.domain.find_character.sources.features.remove_background import (
    remove_background,
)
from typing import Optional
from ad_fast_api.snippets.sources.save_dict import dict_to_file


def save_bounding_box(
    bounding_box: BoundingBox,
    base_path: Path,
):
    to_save_dict = bounding_box.model_dump(mode="json")
    bounding_box_file_name = cw.BOUNDING_BOX_FILE_NAME
    bounding_box_file_path = base_path.joinpath(bounding_box_file_name)
    dict_to_file(
        to_save_dict=to_save_dict,
        file_path=bounding_box_file_path,
    )


# cv2는 cpu bound 작업이므로 asyncio를 사용하지 않음
def cv2_save_image(
    image: np.ndarray,
    image_name: str,
    base_path: Path,
):
    image_path = base_path.joinpath(image_name)
    cv2.imwrite(image_path.as_posix(), image)


def crop_and_segment_character(
    ad_id: str,
    bounding_box: BoundingBox,
    logger: Logger,
    base_path: Optional[Path] = None,
):
    base_path = base_path or cw.get_base_path(ad_id=ad_id)

    cropped_image = crop_image(
        base_path=base_path,
        bounding_box=bounding_box,
    )

    cv2_save_image(
        image=cropped_image,
        image_name=cw.CROPPED_IMAGE_NAME,
        base_path=base_path,
    )

    mask_image = segment_character(
        img=cropped_image,
        logger=logger,
    )

    cv2_save_image(
        image=mask_image,
        image_name=cw.MASK_IMAGE_NAME,
        base_path=base_path,
    )

    removed_bg_image = remove_background(
        cropped_image=cropped_image,
        mask_image=mask_image,
    )

    cv2_save_image(
        image=removed_bg_image,
        image_name=cw.CUTOUT_CHARACTER_IMAGE_NAME,
        base_path=base_path,
    )
