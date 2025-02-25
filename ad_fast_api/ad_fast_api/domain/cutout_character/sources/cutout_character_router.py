from fastapi import APIRouter, UploadFile
from ad_fast_api.workspace.sources import conf_workspace as cw
from ad_fast_api.snippets.sources.ad_http_exception import handle_operation_async
from ad_fast_api.domain.cutout_character.sources.features.cutout_character_feature import (
    save_cutout_image,
)
from ad_fast_api.snippets.sources.ad_logger import setup_logger


router = APIRouter()


@router.post("/cutout_character")
async def cutout_character(
    ad_id: str,
    cutout_character_file: UploadFile,
):
    base_path = cw.get_base_path(ad_id=ad_id)
    logger = setup_logger(base_path=base_path)

    await handle_operation_async(
        save_cutout_image,
        file=cutout_character_file,
        base_path=base_path,
        logger=logger,
    )
