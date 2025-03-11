from fastapi import APIRouter, UploadFile, File
from ad_fast_api.domain.upload_drawing.sources.features.upload_drawing_feature import (
    save_origin_image_async,
    detect_character,
)
from ad_fast_api.snippets.sources.ad_http_exception import handle_operation_async
from ad_fast_api.domain.upload_drawing.sources.upload_drawing_schema import (
    UploadDrawingResponse,
)


router = APIRouter()


@router.post("/upload_drawing")
async def upload_drawing(
    file: UploadFile = File(...),
) -> UploadDrawingResponse:
    ad_id = await handle_operation_async(
        save_origin_image_async,
        file=file,
        status_code=500,
    )
    bounding_box = await handle_operation_async(
        detect_character,
        ad_id=ad_id,
        status_code=501,
    )
    bounding_box_dict = bounding_box.model_dump(mode="json")

    return UploadDrawingResponse(
        ad_id=ad_id,
        bounding_box=bounding_box_dict,
    )


if __name__ == "__main__":
    import asyncio
    from ad_fast_api.workspace.testings import mock_conf_workspace as mcw
    from io import BytesIO
    from unittest.mock import patch
    import ad_fast_api.domain.upload_drawing.sources.features.detect_character as _detect_character
    import ad_fast_api.domain.upload_drawing.sources.features.upload_drawing_feature as upload_drawing_feature

    base_path = mcw.TMP_WORKSPACE_FILES

    origin_image_path = mcw.REQUEST_FILES_PATH / "upload_image.png"
    with open(origin_image_path, "rb") as f:
        origin_image_bytes = f.read()

    upload_file = UploadFile(
        filename="upload_image.png",
        file=BytesIO(origin_image_bytes),
    )

    with patch.object(
        upload_drawing_feature,
        "create_base_dir",
        return_value=base_path,
    ), patch.object(
        upload_drawing_feature,
        "get_base_path",
        return_value=base_path,
    ), patch.object(
        _detect_character,
        "DETECT_CHARACTER_TORCHSERVE_URL",
        new="http://localhost:8080/predictions/drawn_humanoid_detector",
    ):
        asyncio.run(
            upload_drawing(
                file=upload_file,
            )
        )
