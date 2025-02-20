from fastapi import APIRouter, UploadFile, File
from ad_fast_api.domain.upload_drawing.sources.features.configure_work_dir import (
    save_image,
)
from ad_fast_api.domain.upload_drawing.sources.features.detect_character import (
    detect_character,
)
from typing import Dict, Any
from ad_fast_api.snippets.sources.ad_http_exception import handle_operation


router = APIRouter()


@router.post("/upload_drawing")
async def upload_drawing(file: UploadFile = File(...)) -> Dict[str, Any]:
    ad_id = await handle_operation(save_image, file=file)
    bounding_box = await handle_operation(detect_character, ad_id=ad_id)
    bounding_box_dict = bounding_box.model_dump(mode="json")

    return {
        "ad_id": ad_id,
        "bounding_box": bounding_box_dict,
    }
