from fastapi import APIRouter
from fastapi.responses import FileResponse
from ad_fast_api.domain.schema.sources.schemas import BoundingBox
from ad_fast_api.domain.find_character.sources.features.find_character_feature import (
    crop_and_segment_character,
    save_bounding_box,
)
from ad_fast_api.workspace.sources import conf_workspace as cw
from ad_fast_api.snippets.sources.ad_logger import setup_logger
from ad_fast_api.snippets.sources.ad_http_exception import handle_operation


router = APIRouter()


@router.post(
    "/find_character",
    response_class=FileResponse,
    responses={
        200: {
            "content": {"image/png": {}},
            "description": "Cutout character masked image file.",
        }
    },
)
def find_character(
    ad_id: str,
    bounding_box: BoundingBox,
) -> FileResponse:
    base_path = cw.get_base_path(ad_id=ad_id)
    handle_operation(
        save_bounding_box,
        bounding_box=bounding_box,
        base_path=base_path,
        status_code=500,
    )

    logger = setup_logger(base_path=base_path)
    handle_operation(
        crop_and_segment_character,
        ad_id=ad_id,
        bounding_box=bounding_box,
        base_path=base_path,
        logger=logger,
        status_code=501,
    )

    cutout_character_image_path = base_path.joinpath(cw.CUTOUT_CHARACTER_IMAGE_NAME)
    return FileResponse(cutout_character_image_path.as_posix())


if __name__ == "__main__":
    from ad_fast_api.workspace.testings import mock_conf_workspace as mcw
    from unittest.mock import patch
    import yaml

    ad_id = mcw.TMP_AD_ID
    base_path = mcw.TMP_WORKSPACE_FILES

    with open(base_path / cw.BOUNDING_BOX_FILE_NAME, "r") as f:
        bounding_box_dict = yaml.safe_load(f)

    bounding_box = BoundingBox(**bounding_box_dict)

    with patch.object(
        cw,
        "get_base_path",
        return_value=base_path,
    ):
        file_response = find_character(
            ad_id=ad_id,
            bounding_box=bounding_box,
        )
        print(file_response)
