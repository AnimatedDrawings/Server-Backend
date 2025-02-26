from fastapi import APIRouter
from fastapi.responses import FileResponse
from ad_fast_api.snippets.sources.ad_http_exception import handle_operation


router = APIRouter()


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
