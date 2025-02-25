from fastapi import UploadFile
from pathlib import Path
from logging import Logger
from ad_fast_api.domain.cutout_character.sources.features import (
    save_cutout_image as sci,
    configure_skeleton as cs,
)


async def save_cutout_image(
    file: UploadFile,
    base_path: Path,
    logger: Logger,
):
    await sci.save_cutout_character_image_async(
        file=file,
        base_path=base_path,
    )
    result = sci.resize_cutout_image(
        base_path=base_path,
        logger=logger,
    )
    if result is None:
        return
    cropped_image, cutout_image = result

    sci.recreate_mask_image(
        cutout_image=cutout_image,  # type: ignore
        base_path=base_path,
        logger=logger,
    )

    await cs.get_skeleton_async(
        cropped_image=cropped_image,
        logger=logger,
    )
