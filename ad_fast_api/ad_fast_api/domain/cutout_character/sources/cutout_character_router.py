from fastapi import APIRouter, UploadFile, File
from ad_fast_api.workspace.sources import conf_workspace as cw
from ad_fast_api.snippets.sources.ad_http_exception import (
    handle_operation_async,
    handle_operation,
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


if __name__ == "__main__":
    import asyncio
    from io import BytesIO
    from ad_fast_api.workspace.testings import mock_conf_workspace as mcw
    from ad_fast_api.domain.cutout_character.sources.features import configure_skeleton
    from unittest.mock import patch

    ad_id = mcw.TMP_AD_ID
    base_path = mcw.TMP_WORKSPACE_FILES
    cutout_character_image_path = (
        mcw.REQUEST_FILES_PATH / cw.CUTOUT_CHARACTER_IMAGE_NAME
    )
    with open(cutout_character_image_path, "rb") as f:
        cutout_character_image_bytes = f.read()

    upload_file = UploadFile(
        filename=cutout_character_image_path.name,
        file=BytesIO(cutout_character_image_bytes),
    )

    with patch.object(
        cw,
        "get_base_path",
        return_value=base_path,
    ), patch.object(
        configure_skeleton,
        "GET_SKELETON_TORCHSERVE_URL",
        new="http://localhost:8080/predictions/drawn_humanoid_pose_estimator",
    ):
        response = asyncio.run(
            cutout_character(
                ad_id=ad_id,
                file=upload_file,
            )
        )
        print(response.model_dump(mode="json"))
