from fastapi import APIRouter, UploadFile, File
from ad_fast_api.domain.upload_drawing.sources.features.upload_drawing_feature import (
    save_origin_image_async,
    detect_character,
)
from typing import Dict, Any
from ad_fast_api.snippets.sources.ad_http_exception import handle_operation_async
from ad_fast_api.domain.upload_drawing.sources.upload_drawing_schema import (
    UploadDrawingResponse,
)


router = APIRouter()


@router.post("/upload_drawing")
async def upload_drawing(file: UploadFile = File(...)) -> UploadDrawingResponse:
    ad_id = await handle_operation_async(
        save_origin_image_async, file=file, status_code=500
    )
    bounding_box = await handle_operation_async(
        detect_character, ad_id=ad_id, status_code=501
    )
    bounding_box_dict = bounding_box.model_dump(mode="json")

    return UploadDrawingResponse(
        ad_id=ad_id,
        bounding_box=bounding_box_dict,
    )
