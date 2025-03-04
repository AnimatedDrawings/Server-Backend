from fastapi import APIRouter
from fastapi.responses import FileResponse
from ad_fast_api.snippets.sources.ad_http_exception import (
    handle_operation,
    handle_operation_async,
)
from ad_fast_api.domain.make_animation.sources.features.make_animation_feature import (
    check_make_animation_info,
    prepare_make_animation,
    image_to_animation,
)
from ad_fast_api.workspace.sources.conf_workspace import get_base_path
from ad_fast_api.domain.make_animation.sources.errors.make_animation_500_status import (
    NOT_FOUND_ANIMATION_FILE,
)


router = APIRouter()


@router.post(
    "/make_animation",
    response_class=FileResponse,
    responses={
        200: {
            "content": {"image/gif": {}},
            "description": "Animation gif file.",
        }
    },
)
async def make_animation(
    ad_id: str,
    ad_animation: str,
):
    base_path = get_base_path(ad_id=ad_id)

    relative_video_file_path = handle_operation(
        check_make_animation_info,
        base_path=base_path,
        ad_animation=ad_animation,
        status_code=500,
    )

    video_file_path = base_path.joinpath(relative_video_file_path)
    file_response = FileResponse(
        video_file_path.as_posix(),
        media_type="image/gif",
    )
    if relative_video_file_path is None:
        return file_response

    animated_drawings_mvc_cfg_path = handle_operation(
        prepare_make_animation,
        ad_id=ad_id,
        base_path=base_path,
        ad_animation=ad_animation,
        relative_video_file_path=relative_video_file_path,
        status_code=501,
    )

    response = handle_operation_async(
        image_to_animation,
        animated_drawings_mvc_cfg_path=animated_drawings_mvc_cfg_path,
        status_code=502,
    )

    video_file_path = base_path.joinpath(relative_video_file_path)
    if not video_file_path.exists():
        raise NOT_FOUND_ANIMATION_FILE

    return file_response
