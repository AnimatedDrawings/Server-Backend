from fastapi import APIRouter, UploadFile, File
from ad_fast_api.workspace.sources import conf_workspace as cw
from ad_fast_api.snippets.sources.ad_http_exception import (
    handle_operation_async,
)
from ad_fast_api.domain.cutout_character.sources.features.cutout_character_feature import (
    save_cutout_image_async,
    configure_skeleton_async,
    create_cutout_character_response,
)
from ad_fast_api.snippets.sources.ad_logger import setup_logger
from ad_fast_api.domain.cutout_character.sources.cutout_character_schema import (
    CutoutCharacterResponse,
)


router = APIRouter()


@router.post("/cutout_character")
async def cutout_character(
    ad_id: str,
    file: UploadFile = File(...),
) -> CutoutCharacterResponse:
    base_path = cw.get_base_path(ad_id=ad_id)
    logger = setup_logger(base_path=base_path)

    await handle_operation_async(
        save_cutout_image_async,
        file=file,
        base_path=base_path,
        logger=logger,
        status_code=500,
    )

    char_cfg_dict = await handle_operation_async(
        configure_skeleton_async,
        base_path=base_path,
        logger=logger,
        status_code=501,
    )

    response = create_cutout_character_response(char_cfg_dict)
    return response
