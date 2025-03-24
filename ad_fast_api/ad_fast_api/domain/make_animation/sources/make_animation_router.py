import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, FastAPI
from fastapi.responses import FileResponse
from fastapi.openapi.utils import get_openapi
from ad_fast_api.snippets.sources.ad_http_exception import (
    handle_operation,
    handle_operation_async,
)
from ad_fast_api.domain.make_animation.sources.features.make_animation_feature import (
    check_make_animation_info,
    prepare_make_animation,
    image_to_animation_async,
    get_file_response,
)
from ad_fast_api.workspace.sources.conf_workspace import get_base_path
from ad_fast_api.domain.make_animation.sources.errors.make_animation_500_status import (
    NOT_FOUND_ANIMATION_FILE,
)
from ad_fast_api.snippets.sources import ad_websocket
from ad_fast_api.snippets.sources.ad_logger import setup_logger


router = APIRouter()


@router.websocket("/make_animation")
async def make_animation_websocket(
    websocket: WebSocket,
    ad_id: str,
):
    base_path = get_base_path(ad_id=ad_id)
    logger = setup_logger(base_path=base_path)
    await ad_websocket.websocket_async(
        websocket=websocket,
        logger=logger,
        operation=make_animation_async,
    )

    # await websocket.accept()
    # await websocket.send_json({"type": "ping"})
    # await websocket.close()


# @router.post(
#     "/make_animation",
#     response_class=FileResponse,
#     responses={
#         200: {
#             "content": {"image/gif": {}},
#             "description": "Animation gif file.",
#         }
#     },
# )
# async def make_animation(
#     ad_id: str,
#     ad_animation: str,
# ):
#     base_path = get_base_path(ad_id=ad_id)

#     is_video_file_exists, relative_video_file_path = handle_operation(
#         check_make_animation_info,
#         base_path=base_path,
#         ad_animation=ad_animation,
#         status_code=500,
#     )

#     if is_video_file_exists:
#         file_response = get_file_response(
#             base_path=base_path,
#             relative_video_file_path=relative_video_file_path,
#         )
#         return file_response

#     animated_drawings_mvc_cfg_path = handle_operation(
#         prepare_make_animation,
#         ad_id=ad_id,
#         base_path=base_path,
#         ad_animation=ad_animation,
#         relative_video_file_path=relative_video_file_path,
#         status_code=501,
#     )

#     await handle_operation_async(
#         image_to_animation_async,
#         base_path=base_path,
#         animated_drawings_mvc_cfg_path=animated_drawings_mvc_cfg_path,
#         relative_video_file_path=relative_video_file_path,
#         status_code=502,
#     )

#     video_file_path = base_path.joinpath(relative_video_file_path)
#     if not video_file_path.exists():
#         raise NOT_FOUND_ANIMATION_FILE

#     file_response = get_file_response(
#         base_path=base_path,
#         relative_video_file_path=relative_video_file_path,
#     )
#     return file_response


def make_animation_openapi(app: FastAPI):
    return ad_websocket.custom_openapi(
        app=app,
        paths="/test/make_animation",
        method="post",
        summary="WebSocket /test/make_animation Endpoint",
        description=(
            "이 엔드포인트는 웹소켓 연결을 위한 엔드포인트입니다. 실제 연결은 웹소켓 프로토콜을 통해 이루어지며, "
            "HTTP GET 라우터는 단지 문서화 목적으로만 포함되어 있습니다."
        ),
        responses={
            "101": {  # 101 Switching Protocols
                "description": "웹소켓 연결 시작 (Switching Protocols)"
            }
        },
    )
