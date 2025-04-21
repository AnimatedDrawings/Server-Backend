from pathlib import Path
from ad_fast_api.domain.make_animation.sources.features.prepare_make_animation import (
    create_animated_drawing_dict,
    create_mvc_config,
    save_mvc_config,
)
from ad_fast_api.snippets.sources.ad_env import get_ad_env
from ad_fast_api.workspace.sources.conf_workspace import (
    FILES_DIR_NAME,
    MVC_CFG_FILE_NAME,
)
from ad_fast_api.domain.make_animation.sources.features.image_to_animation import (
    is_finish_render,
    cancel_render_async,
)
from ad_fast_api.snippets.sources.ad_websocket import check_connection
from fastapi.responses import FileResponse
from fastapi import WebSocket, WebSocketDisconnect
from logging import Logger
import asyncio


def get_file_response(
    base_path: Path,
    relative_video_file_path: Path,
) -> FileResponse:
    video_file_path = base_path.joinpath(relative_video_file_path)
    file_response = FileResponse(
        video_file_path.as_posix(),
        media_type="image/gif",
    )
    return file_response


def prepare_make_animation(
    ad_id: str,
    base_path: Path,
    ad_animation: str,
    relative_video_file_path: Path,
) -> Path:
    animated_drawings_workspace_path = Path(
        get_ad_env().animated_drawings_workspace_dir
    )
    animated_drawings_base_path = animated_drawings_workspace_path.joinpath(
        FILES_DIR_NAME
    ).joinpath(ad_id)

    animated_drawings_dict = create_animated_drawing_dict(
        animated_drawings_base_path=animated_drawings_base_path,
        animated_drawings_workspace_path=animated_drawings_workspace_path,
        ad_animation=ad_animation,
    )

    video_file_path = animated_drawings_base_path.joinpath(relative_video_file_path)

    mvc_cfg_dict = create_mvc_config(
        animated_drawings_dict=animated_drawings_dict,
        video_file_path=video_file_path,
        ad_animation=ad_animation,
    )
    save_mvc_config(
        mvc_cfg_file_name=MVC_CFG_FILE_NAME,
        mvc_cfg_dict=mvc_cfg_dict,
        base_path=base_path,
    )

    animated_drawings_mvc_cfg_path = animated_drawings_base_path.joinpath(
        MVC_CFG_FILE_NAME
    )
    return animated_drawings_mvc_cfg_path


def period_finish_render(
    timer: int,
    period: int,
) -> bool:
    reward_advertisement_time = 20
    return reward_advertisement_time < timer and timer % period == 0


# 주기적으로 렌더링 완료 확인 및 연결 상태 확인
async def check_connection_and_rendering(
    job_id: str,
    base_path: Path,
    relative_video_file_path: Path,
    websocket: WebSocket,
    logger: Logger,
):
    connection_timer = 0
    connection_period = 5  # 5초 주기로 클라이언트 연결 확인
    finish_render_period = 2
    render_timer = 0
    max_render_time = 60 * 3  # 렌더링 최대 3분 대기
    video_file_path = base_path.joinpath(relative_video_file_path)

    try:
        while render_timer < max_render_time:
            await check_connection(
                timer=connection_timer,
                period=connection_period,
                websocket=websocket,
                logger=logger,
            )
            connection_timer += 1

            if period_finish_render(
                timer=render_timer,
                period=finish_render_period,
            ) and await is_finish_render(
                job_id=job_id,
                logger=logger,
                timeout_seconds=7,
            ):
                if not video_file_path.exists():
                    msg = "Rendering has been completed, but the video file does not exist."
                    logger.error(msg)
                    raise Exception(msg)
                logger.info("Rendering has been completed.")
                return
            render_timer += 1

            await asyncio.sleep(1)
        else:
            msg = "Rendering time has exceeded the limit."
            raise Exception(msg)
    except WebSocketDisconnect as e:
        msg = "The websocket connection with the client has been terminated"
        logger.error(f"{msg}: {e}")
        await cancel_render_async(job_id=job_id, logger=logger)
        raise Exception(msg)
    except Exception as e:
        msg = f"An error occurred while processing the job : {e}"
        logger.error(msg)
        await cancel_render_async(job_id=job_id, logger=logger)
        raise Exception(msg)
