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
    get_cropped_image,
)
from ad_fast_api.domain.cutout_character.sources.cutout_character_schema import (
    CutoutCharacterResponse,
)
from ad_fast_api.domain.schema.sources.schemas import Joints


async def save_cutout_image_async(
    file: UploadFile,
    base_path: Path,
    logger: Logger,
):
    await save_cutout_character_image_async(
        file=file,
        base_path=base_path,
    )
    cutout_image = resize_cutout_image(
        base_path=base_path,
        logger=logger,
    )

    recreate_mask_image(
        cutout_image=cutout_image,  # type: ignore
        base_path=base_path,
        logger=logger,
    )


async def configure_skeleton_async(
    base_path: Path,
    logger: Logger,
) -> dict:
    cropped_image = get_cropped_image(
        base_path=base_path,
        logger=logger,
    )

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
    char_cfg_dict = save_char_cfg(
        skeleton=skeleton,
        cropped_image=cropped_image,
        base_path=base_path,
    )

    return char_cfg_dict


def create_cutout_character_response(
    char_cfg_dict: dict,
) -> CutoutCharacterResponse:
    return CutoutCharacterResponse(
        char_cfg=Joints(**char_cfg_dict),
    )
