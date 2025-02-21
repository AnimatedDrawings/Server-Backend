from fastapi import APIRouter
from ad_fast_api.domain.schema.sources.schemas import BoundingBox
from ad_fast_api.domain.ad_features.sources.bounding_box_feature import (
    save_bounding_box,
)
from ad_fast_api.workspace.sources import conf_workspace as cw

router = APIRouter()


@router.get("/find_character")
async def find_character(
    ad_id: str,
    bounding_box: BoundingBox,
):
    base_path = cw.get_base_path(ad_id=ad_id)
    save_bounding_box(bounding_box, base_path)
