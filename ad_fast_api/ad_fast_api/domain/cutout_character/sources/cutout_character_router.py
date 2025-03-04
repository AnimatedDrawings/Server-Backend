from fastapi import APIRouter, UploadFile
from ad_fast_api.workspace.sources import conf_workspace as cw
from ad_fast_api.snippets.sources.ad_http_exception import handle_operation_async
from ad_fast_api.domain.cutout_character.sources.features.cutout_character_feature import (
    save_cutout_image,
    configure_skeleton,
)
from ad_fast_api.snippets.sources.ad_logger import setup_logger
from ad_fast_api.domain.cutout_character.sources.cutout_character_schema import (
    CutoutCharacterResponse,
)


router = APIRouter()


@router.post("/cutout_character")
async def cutout_character(
    ad_id: str,
    cutout_character_file: UploadFile,
) -> CutoutCharacterResponse:
    base_path = cw.get_base_path(ad_id=ad_id)
    logger = setup_logger(base_path=base_path)

    cropped_image = await handle_operation_async(
        save_cutout_image,
        file=cutout_character_file,
        base_path=base_path,
        logger=logger,
        status_code=500,
    )

    char_cfg_dict = await handle_operation_async(
        configure_skeleton,
        cropped_image=cropped_image,
        base_path=base_path,
        logger=logger,
        status_code=501,
    )

    return CutoutCharacterResponse(
        char_cfg=char_cfg_dict,
    )
