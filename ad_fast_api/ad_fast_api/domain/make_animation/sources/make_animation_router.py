from fastapi import APIRouter
from fastapi.responses import FileResponse
from ad_fast_api.snippets.sources.ad_http_exception import handle_operation


router = APIRouter()


def make_animation_garlic_feature():
    from ad_fast_api.workspace.sources.conf_workspace import get_base_path
    from ad_fast_api.domain.make_animation.sources.features.make_animation_feature import (
        check_make_animation_info,
        prepare_make_animation,
        image_to_animation,
    )
    from ad_fast_api.domain.make_animation.sources.make_animation_schema import (
        ADAnimation,
    )

    ad_id = "result_garlic"
    base_path = get_base_path(ad_id=ad_id)
    ad_animation = ADAnimation.dab.value

    relative_video_file_path = check_make_animation_info(
        base_path=base_path,
        ad_animation=ad_animation,
    )

    if relative_video_file_path is None:
        print("video file exists.. not making animation")
        return

    mvc_cfg_path = prepare_make_animation(
        ad_id=ad_id,
        base_path=base_path,
        ad_animation=ad_animation,
        relative_video_file_path=relative_video_file_path,
    )

    image_to_animation(
        animated_drawings_mvc_cfg_path=mvc_cfg_path,
    )


@router.get("/test_make_animation")
def make_animation_garlic():
    make_animation_garlic_feature()


@router.post("/make_animation")
def make_animation(
    ad_id: str,
    ad_animation: str,
):
    pass
    # handle_operation(
    #     check_available_animation,
    #     ad_animation=ad_animation,
    # )

    # FileResponse(video_file_path.as_posix(), media_type="image/gif")
