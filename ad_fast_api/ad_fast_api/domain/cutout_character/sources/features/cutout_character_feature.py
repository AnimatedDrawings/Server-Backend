from fastapi import UploadFile
from pathlib import Path
from logging import Logger
from ad_fast_api.domain.cutout_character.sources.features.save_cutout_image import (
    save_cutout_character_image_async,
    resize_cutout_image,
    recreate_mask_image,
)
from ad_fast_api.domain.cutout_character.sources.features.configure_skeleton import (
    get_pose_result_async,
    check_pose_results,
    make_skeleton,
    save_char_cfg,
)
from cv2.typing import MatLike
from typing import Optional


async def save_cutout_image(
    file: UploadFile,
    base_path: Path,
    logger: Logger,
) -> MatLike:
    await save_cutout_character_image_async(
        file=file,
        base_path=base_path,
    )
    cropped_image, cutout_image = resize_cutout_image(
        base_path=base_path,
        logger=logger,
    )

    recreate_mask_image(
        cutout_image=cutout_image,  # type: ignore
        base_path=base_path,
        logger=logger,
    )

    return cropped_image


async def configure_skeleton(
    cropped_image: MatLike,
    base_path: Path,
    logger: Logger,
):
    pose_result = await get_pose_result_async(
        cropped_image=cropped_image,
        logger=logger,
    )
    kpts = check_pose_results(
        pose_results=pose_result,  # type: ignore
        logger=logger,
    )
    skeleton = make_skeleton(
        kpts=kpts,
    )
    save_char_cfg(
        skeleton=skeleton,
        cropped_image=cropped_image,
        base_path=base_path,
    )
