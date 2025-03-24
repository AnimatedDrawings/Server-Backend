import asyncio
from logging import Logger
import pytest
from fastapi import FastAPI
from fastapi.websockets import WebSocket
from ad_fast_api.snippets.sources.ad_websocket import (
    get_pong_response,
    is_valid_response,
    retry_websocket,
    websocket_async,
    custom_openapi,
)
from ad_fast_api.snippets.testings.mock_ad_websocket import (
    DummyWebSocket,
    DummyLogger,
)


@pytest.mark.asyncio
async def test_get_pong_response():
    ws = DummyWebSocket(responses=[{"type": "pong"}])
    response = await get_pong_response(ws, timeout=1)
    assert response == {"type": "pong"}


def test_is_valid_response():
    valid_response = {"type": "pong"}
    invalid_response = {"type": "ping"}
    assert is_valid_response(valid_response) is True
    assert is_valid_response(invalid_response) is False


# retry_websocket 함수 테스트: 처음 두 번 잘못된 응답, 세 번째에 올바른 "pong" 응답
@pytest.mark.asyncio
async def test_retry_websocket_success_after_retries():
    responses = [
        {"type": "invalid"},
        {"type": "no_pong"},
        {"type": "pong"},
    ]
    ws = DummyWebSocket(responses=responses)
    logger = DummyLogger()
    await retry_websocket(ws, logger, max_retries=3)
    # 웹소켓이 닫히지 않았어야 함
    assert not ws.closed
    # 에러 로그들이 기록되었는지 확인
    error_logs = [log for level, log in logger.logs if level == "error"]
    assert any("유효하지 않은 응답" in log for log in error_logs)


# retry_websocket 함수 테스트: 타임아웃 발생 시 웹소켓이 닫혀야 함
@pytest.mark.asyncio
async def test_retry_websocket_timeout(monkeypatch):
    async def never_return():
        await asyncio.sleep(10)  # 긴 시간 동안 응답 없음

    ws = DummyWebSocket(responses=[])
    # receive_json 메소드를 타임아웃 시나리오로 대체
    ws.receive_json = never_return
    logger = DummyLogger()
    await retry_websocket(ws, logger, max_retries=2)
    assert ws.closed
    error_logs = [log for level, log in logger.logs if level == "error"]
    assert any("최대 재시도 횟수 초과" in log for log in error_logs)


# websocket_async 함수 테스트: send_json에서 예외 발생 시 루프가 종료되는지 확인
@pytest.mark.asyncio
async def test_websocket_async_send_ping_failure():
    ws = DummyWebSocket(
        responses=[{"type": "pong"}], send_json_side_effect=Exception("send 실패")
    )
    logger = DummyLogger()
    await websocket_async(ws, logger)
    error_logs = [log for level, log in logger.logs if level == "error"]
    assert any("Ping 메시지 전송 중 오류 발생" in log for log in error_logs)


# custom_openapi 함수 테스트
def test_custom_openapi():
    app = FastAPI()
    paths = "/ws"
    method = "get"
    summary = "테스트 웹소켓"
    description = "테스트용 웹소켓 엔드포인트 문서"
    responses = {"200": {"description": "성공"}}

    schema = custom_openapi(app, paths, method, summary, description, responses)
    assert paths in schema["paths"]
    assert method in schema["paths"][paths]
    assert schema["paths"][paths][method]["summary"] == summary
