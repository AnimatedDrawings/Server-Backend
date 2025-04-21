from pathlib import Path
from zero import AsyncZeroClient
from typing import Optional
from logging import Logger
from ad_fast_api.domain.make_animation.sources.make_animation_schema import (
    WebSocketMessage,
    WebSocketType,
    create_websocket_message,
)
from ad_fast_api.snippets.sources.ad_dictionary import get_value_from_dict


# internal port env 사용하기
def get_zero_client(
    host: str = "animated_drawings",
    port: int = 8001,
    timeout_seconds: Optional[float] = None,
) -> AsyncZeroClient:
    timeout = int(timeout_seconds * 1000) if timeout_seconds != None else 3000

    return AsyncZeroClient(
        host,
        port,
        default_timeout=timeout,
    )


async def start_render_async(
    animated_drawings_mvc_cfg_path: Path,
    logger: Logger,
    timeout_seconds: Optional[float] = None,
) -> WebSocketMessage:
    try:
        response = await get_zero_client(timeout_seconds=timeout_seconds).call(
            "start_render",
            animated_drawings_mvc_cfg_path.as_posix(),
        )

        if response is None:
            msg = "Failed to start animation rendering, no return value."
            logger.error(msg)
            return create_websocket_message(
                WebSocketType.ERROR,
                msg,
            )

        type = response.get("type")
        job_id = get_value_from_dict(
            key_list=["data", "job_id"],
            from_dict=response,
        )
        if type == WebSocketType.RUNNING and job_id is not None:
            logger.info("Animation rendering started.")
            return create_websocket_message(
                WebSocketType.RUNNING,
                "Animation rendering started.",
                data={
                    "job_id": job_id,
                },
            )
        elif type == WebSocketType.FULL_JOB:
            msg = "Animation rendering queue is full."
            logger.info(msg)
            return create_websocket_message(
                WebSocketType.FULL_JOB,
                "The current workload is high. Please try again later.",
            )
        else:
            msg = (
                f"Failed to start animation rendering, unknown return value. {response}"
            )
            logger.error(msg)
            return create_websocket_message(
                WebSocketType.ERROR,
                msg,
            )
    except Exception as e:
        msg = f"Failed to start animation rendering, {e}"
        logger.error(msg)
        return create_websocket_message(
            WebSocketType.ERROR,
            msg,
        )


async def cancel_render_async(
    job_id: str,
    logger: Logger,
    timeout_seconds: Optional[float] = None,
):
    try:
        response = await get_zero_client(timeout_seconds=timeout_seconds).call(
            "cancel_render",
            job_id,
        )

        if response is None:
            msg = "Failed to cancel animation rendering, no return value."
            logger.error(msg)
            return

        type = response.get("type")
        if type == "TERMINATE":
            logger.info("Animation rendering has been canceled.")
            return
        else:
            msg = f"Failed to cancel animation rendering, unknown return value. {response}"
            logger.error(msg)
            return
    except Exception as e:
        msg = f"Failed to cancel animation rendering, {e}"
        logger.error(msg)
        return


async def is_finish_render(
    job_id: str,
    logger: Logger,
    timeout_seconds: Optional[float] = None,
) -> bool:
    try:
        response = await get_zero_client(timeout_seconds=timeout_seconds).call(
            "is_finish_render",
            job_id,
        )

        if response is None:
            msg = "Failed to check if animation rendering is finished, no return value."
            logger.error(msg)
            raise Exception(msg)

        type = response.get("type")
        if type == "TERMINATE":
            logger.info("Animation rendering is finished.")
            return True
        elif type == "RUNNING":
            logger.info("Animation rendering is in progress.")
            return False
        else:
            msg = f"Failed to check if animation rendering is finished, unknown return value. {response}"
            logger.error(msg)
            raise Exception(msg)
    except Exception as e:
        msg = (
            f"Failed to check if animation rendering is finished, connection error. {e}"
        )
        logger.error(msg)
        raise Exception(msg)
