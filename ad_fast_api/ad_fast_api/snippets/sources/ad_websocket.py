import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.openapi.utils import get_openapi
from logging import Logger


async def get_pong_response(
    websocket: WebSocket,
    timeout: int = 3,
):
    response = await asyncio.wait_for(
        websocket.receive_json(),
        timeout=timeout,
    )

    return response


def is_valid_response(response: dict):
    return response.get("type") == "pong"


async def retry_websocket(
    websocket: WebSocket,
    logger: Logger,
    max_retries: int = 3,
):
    retry_count = 0

    while retry_count < max_retries:
        try:
            response = await get_pong_response(websocket)
            if not is_valid_response(response):
                msg = f"유효하지 않은 응답 (시도 {retry_count+1}/{max_retries}) : {response}"
                logger.error(msg)

                retry_count += 1
                if max_retries <= retry_count:
                    await websocket.close(
                        code=1000,
                        reason="유효하지 않은 응답 - 최대 재시도 횟수 초과",
                    )
                    break
            else:
                print("pong 응답:", response)
                break  # 성공적인 응답을 받았으므로 재시도 루프 종료
        except asyncio.TimeoutError:
            # 타임아웃 발생 시, 재시도 횟수를 증가시킵니다.
            retry_count += 1
            print(f"pong 응답 지연 (시도 {retry_count}/{max_retries})")

            if retry_count >= max_retries:
                msg = f"최대 재시도 횟수 초과 - 연결 종료 (시도 {retry_count}/{max_retries})"
                logger.error(msg)
                await websocket.close(
                    code=1001,
                    reason="pong 응답 지연 - 최대 재시도 횟수 초과",
                )
                break


async def websocket_async(websocket: WebSocket, logger: Logger):
    """
    웹소켓 연결 수락 후, 주기적으로 "ping" 메시지를 전송하고 "pong" 응답을 대기하며
    연결 상태를 유지하는 메소드입니다.
    매 5초마다 "ping" 메시지를 전송하며, 최대 3번의 재시도를 통해 "pong" 응답을 확인합니다.
    """
    try:
        await websocket.accept()
        logger.info("웹소켓 연결이 성공적으로 수락되었습니다.")
    except Exception as e:
        logger.exception("웹소켓 연결 수락 중 오류 발생: %s", e)
        return

    try:
        while True:
            try:
                await websocket.send_json({"type": "ping"})
            except Exception as send_err:
                logger.error("Ping 메시지 전송 중 오류 발생: %s", send_err)
                break

            # "pong" 응답 확인 (최대 3회 재시도)
            try:
                await retry_websocket(websocket, logger, max_retries=3)
            except Exception as retry_err:
                logger.error("pong 응답 처리 중 오류 발생: %s", retry_err)
                break

            # heartbeat 간격: 5초
            await asyncio.sleep(5)
    except WebSocketDisconnect as e:
        logger.info("클라이언트와의 웹소켓 연결이 종료되었습니다: %s", e)
    except Exception as e:
        logger.exception("웹소켓 유지 관리 중 예기치 않은 오류 발생: %s", e)
        await websocket.close(code=1011, reason="서버 내부 오류")


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
