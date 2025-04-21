import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.openapi.utils import get_openapi
from logging import Logger


MAX_RETRIES = 4
TIMEOUT = 3
INTERVAL_SLEEP = 0.3


# 웹소켓 연결
async def accept_websocket(
    websocket: WebSocket,
    logger: Logger,
):
    try:
        await websocket.accept()
        logger.info("The websocket connection has been successfully accepted.")
    except Exception as e:
        msg = "An error occurred while accepting the websocket connection"
        logger.error(f"{msg}: {e}")
        await websocket.close()
        raise Exception(msg)


async def retry_ping(
    websocket: WebSocket,
    logger: Logger,
):
    retry_count = 0

    while retry_count < MAX_RETRIES:
        try:
            await asyncio.wait_for(
                websocket.send_json(
                    {
                        "type": "PING",
                        "message": "",
                        "data": {},
                    }
                ),
                timeout=TIMEOUT,
            )
            logger.debug("ping 메시지 전송")
            return
        except Exception as e:
            retry_count += 1
            msg = f"Ping 메시지 전송 실패 (시도 {retry_count}/{MAX_RETRIES}): {e}"
            logger.warning(msg)
            await asyncio.sleep(INTERVAL_SLEEP)
    else:
        msg = (
            f"Ping 메시지 전송 최대 재시도 횟수 초과 (시도 {retry_count}/{MAX_RETRIES})"
        )
        logger.error(msg)
        raise WebSocketDisconnect(code=1000, reason=msg)


async def retry_pong(
    websocket: WebSocket,
    logger: Logger,
    max_retries: int = MAX_RETRIES,
):
    retry_count = 0

    while retry_count < max_retries:
        try:
            response = await asyncio.wait_for(
                websocket.receive_json(),
                timeout=TIMEOUT,
            )

            if response.get("type") == "PONG":
                logger.debug("PONG 응답 수신")
                return

            retry_count += 1
            msg = f"유효하지 않은 응답 (시도 {retry_count}/{max_retries}) : {response}"
            logger.warning(msg)
            await asyncio.sleep(INTERVAL_SLEEP)
        except Exception as e:
            retry_count += 1
            msg = (
                f"pong 응답 처리 중 오류 발생 (시도 {retry_count}/{max_retries}) : {e}"
            )
            logger.warning(msg)
            await asyncio.sleep(INTERVAL_SLEEP)
    else:
        msg = f"pong 응답 처리 최대 재시도 횟수 초과 (시도 {retry_count}/{max_retries})"
        logger.error(msg)
        raise WebSocketDisconnect(code=1000, reason=msg)


async def check_connection(
    timer: int,
    period: int,
    websocket: WebSocket,
    logger: Logger,
):
    if timer % period == 0:
        logger.debug(f"서버 클라이언트 ping/pong 연결 확인 시작, 현재 {timer}초")
        await retry_ping(websocket, logger)
        await retry_pong(websocket, logger)
        logger.debug(f"서버 클라이언트 ping/pong 연결 확인 완료, 현재 {timer}초")


def custom_openapi(
    app: FastAPI,
    paths: str,
    method: str,
    summary: str,
    description: str,
    responses: dict,
):
    openapi_schema = get_openapi(
        title="My API",
        version="1.0.0",
        routes=app.routes,
    )
    # 웹소켓 엔드포인트에 대한 문서 수동 추가 (HTTP GET 방식으로 표현)
    openapi_schema["paths"][paths] = {
        method: {
            "summary": summary,
            "description": description,
            "responses": responses,
        }
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema
