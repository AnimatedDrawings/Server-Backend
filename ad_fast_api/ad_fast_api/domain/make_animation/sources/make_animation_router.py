from fastapi import APIRouter
from ad_fast_api.snippets.sources.ad_http_exception import handle_operation
from ad_fast_api.domain.make_animation.sources.make_animation_feature import (
    check_available_animation,
)


router = APIRouter()


@router.post("/make_animation")
def make_animation(
    ad_id: str,
    ad_animation: str,
):
    handle_operation(
        check_available_animation,
        ad_animation=ad_animation,
    )
