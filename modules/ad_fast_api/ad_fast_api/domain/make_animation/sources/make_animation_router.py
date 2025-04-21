from fastapi import APIRouter, WebSocket, FastAPI
from fastapi.responses import FileResponse
from ad_fast_api.domain.make_animation.sources.features.make_animation_feature import (
    prepare_make_animation,
    get_file_response,
    check_connection_and_rendering,
)
from ad_fast_api.domain.make_animation.sources.features.check_make_animation_info import (
    check_available_animation,
    get_video_file_path,
)
from ad_fast_api.domain.make_animation.sources.features.image_to_animation import (
    start_render_async,
)
from ad_fast_api.workspace.sources.conf_workspace import get_base_path
from ad_fast_api.snippets.sources.ad_websocket import (
    custom_openapi,
)
from ad_fast_api.snippets.sources.ad_logger import setup_logger
from ad_fast_api.domain.make_animation.sources.errors.make_animation_500_status import (
    NOT_FOUND_ANIMATION_FILE,
)
from ad_fast_api.domain.make_animation.sources.make_animation_schema import (
    WebSocketType,
    create_websocket_message,
)
from ad_fast_api.snippets.sources.ad_dictionary import get_value_from_dict
import logging


router = APIRouter()


@router.websocket("/make_animation")
async def make_animation_websocket(
    websocket: WebSocket,
    ad_id: str,
    ad_animation: str,
):
    """
    웹소켓 연결 수락 후 애니메이션 렌더링 시작 요청을 보냅니다.
    5초마다 ping 메시지와 pong 응답을 주고 받으며, 최대 3번의 재시도를 통해 연결상태를 확인합니다.
    연결이 중단되면 렌더링 중단을 요청합니다.

    렌더링 완료는 1초마다 확인하며, 렌더링 완료 시 파일 전송을 시작합니다.
    파일 전송 완료 시 웹소켓 연결을 종료합니다.
    """
    base_path = get_base_path(ad_id=ad_id)
    logger = setup_logger(ad_id=ad_id, level=logging.DEBUG)

    # 웹소켓 연결
    try:
        await websocket.accept()
        logger.info("The websocket connection has been successfully accepted.")
    except Exception as e:
        msg = "An error occurred while accepting the websocket connection"
        logger.error(f"{msg}: {e}")
        await websocket.close()
        return

    # 애니메이션 이름 유효성 검사
    try:
        check_available_animation(ad_animation, logger)
    except Exception as e:
        await websocket.send_json(
            create_websocket_message(
                type=WebSocketType.ERROR,
                message=str(e),
            )
        )
        await websocket.close()
        return

    # 애니메이션 파일 존재 여부 확인
    video_file_path, relative_video_file_path = get_video_file_path(
        base_path=base_path,
        ad_animation=ad_animation,
        logger=logger,
    )

    if video_file_path.exists():
        await websocket.send_json(
            create_websocket_message(
                type=WebSocketType.COMPLETE,
                message="Animation rendering has been completed.",
                data={
                    "file_path": str(relative_video_file_path),
                },
            )
        )
        await websocket.close()
        return

    # 애니메이션 렌더링 준비
    try:
        animated_drawings_mvc_cfg_path = prepare_make_animation(
            ad_id=ad_id,
            base_path=base_path,
            ad_animation=ad_animation,
            relative_video_file_path=relative_video_file_path,
        )
    except Exception as e:
        logger.error(f"Error preparing make animation: {e}")
        await websocket.send_json(
            create_websocket_message(
                type=WebSocketType.ERROR,
                message=str(e),
            )
        )
        await websocket.close()
        return

    # 애니메이션 렌더링 시작 요청
    start_websocket_message = await start_render_async(
        animated_drawings_mvc_cfg_path=animated_drawings_mvc_cfg_path,
        logger=logger,
    )
    await websocket.send_json(start_websocket_message)
    start_type = start_websocket_message["type"]
    if start_type != WebSocketType.RUNNING:
        await websocket.close()
        return

    # 렌더링 작업 ID 추출
    job_id = get_value_from_dict(
        key_list=["data", "job_id"],
        from_dict=dict(start_websocket_message),
    )
    if job_id is None:
        logger.error("Rendering job ID not found.")
        await websocket.send_json(
            create_websocket_message(
                type=WebSocketType.ERROR,
                message="Rendering job ID not found.",
            )
        )
        await websocket.close()
        return

    # 주기적으로 렌더링 작업 확인
    try:
        await check_connection_and_rendering(
            job_id=job_id,
            websocket=websocket,
            logger=logger,
            base_path=base_path,
            relative_video_file_path=relative_video_file_path,
        )
    except Exception as e:
        await websocket.send_json(
            create_websocket_message(
                type=WebSocketType.ERROR,
                message=str(e),
            )
        )
        await websocket.close()
        return

    # 렌더링 완료, 웹소켓 메시지 전송
    await websocket.send_json(
        create_websocket_message(
            type=WebSocketType.COMPLETE,
            message="Animation rendering has been completed.",
        )
    )
    await websocket.close()


@router.get(
    "/download_animation",
    response_class=FileResponse,
    responses={
        200: {
            "content": {"image/gif": {}},
            "description": "Animation gif file.",
        }
    },
)
async def download_animation(
    ad_id: str,
    ad_animation: str,
) -> FileResponse:
    """
    애니메이션 파일 다운로드
    """
    base_path = get_base_path(ad_id=ad_id)
    logger = setup_logger(ad_id=ad_id)

    video_file_path, relative_video_file_path = get_video_file_path(
        base_path=base_path,
        ad_animation=ad_animation,
        logger=logger,
    )
    if not video_file_path.exists():
        raise NOT_FOUND_ANIMATION_FILE

    file_response = get_file_response(
        base_path=base_path,
        relative_video_file_path=relative_video_file_path,
    )
    # 파일 크기를 계산하여 Content-Length 헤더에 추가합니다.
    file_size = video_file_path.stat().st_size
    file_response.headers["Content-Length"] = str(file_size)
    return file_response


def make_animation_openapi(app: FastAPI):
    return custom_openapi(
        app=app,
        paths="/make_animation",
        method="post",
        summary="WebSocket /make_animation Endpoint",
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
