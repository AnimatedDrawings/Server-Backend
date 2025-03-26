import asyncio
import logging
import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import FastAPI, WebSocketDisconnect
from fastapi.websockets import WebSocket
from ad_fast_api.snippets.sources.ad_websocket import (
    retry_ping,
    retry_pong,
    custom_openapi,
    accept_websocket,
    MAX_RETRIES,
)


@pytest.mark.asyncio
async def test_accept_websocket_success():
    # Given
    mock_websocket = AsyncMock(spec=WebSocket)
    mock_logger = MagicMock()

    # When
    await accept_websocket(mock_websocket, mock_logger)

    # Then
    mock_websocket.accept.assert_called_once()
    mock_logger.info.assert_called_once_with(
        "The websocket connection has been successfully accepted."
    )


@pytest.mark.asyncio
async def test_accept_websocket_failure():
    # Given
    mock_websocket = AsyncMock(spec=WebSocket)
    mock_logger = MagicMock()
    mock_websocket.accept.side_effect = Exception("연결 실패")

    # When/Then
    with pytest.raises(Exception) as exc_info:
        await accept_websocket(mock_websocket, mock_logger)

    assert (
        str(exc_info.value)
        == "An error occurred while accepting the websocket connection"
    )
    mock_websocket.close.assert_called_once()
    mock_logger.error.assert_called_once_with(
        "An error occurred while accepting the websocket connection: 연결 실패"
    )


# retry_ping 함수 테스트
@pytest.mark.asyncio
async def test_retry_ping_success():
    # 웹소켓 모의 객체 생성
    websocket = AsyncMock(spec=WebSocket)
    websocket.send_json = AsyncMock()

    # 로거 모의 객체 생성
    logger = MagicMock(spec=logging.Logger)

    # 함수 실행
    await retry_ping(websocket, logger)

    # 웹소켓의 send_json이 호출되었는지 확인
    websocket.send_json.assert_called_once_with(
        {
            "type": "ping",
            "message": "",
            "data": {},
        }
    )
    # 로거의 error가 호출되지 않았는지 확인
    logger.error.assert_not_called()


@pytest.mark.asyncio
async def test_retry_ping_success_on_second_try():
    # 웹소켓 모의 객체 생성
    websocket = AsyncMock(spec=WebSocket)

    # 첫 번째 호출에서는 예외를 발생시키고, 두 번째 호출에서는 성공하도록 설정
    websocket.send_json = AsyncMock(side_effect=[Exception("첫 번째 시도 실패"), None])

    # 로거 모의 객체 생성
    logger = MagicMock(spec=logging.Logger)

    # 함수 실행
    await retry_ping(websocket, logger)

    # 웹소켓의 send_json이 정확히 2번 호출되었는지 확인
    assert websocket.send_json.call_count == 2

    # 모든 호출이 TYPE_PING과 함께 이루어졌는지 확인
    websocket.send_json.assert_any_call(
        {
            "type": "ping",
            "message": "",
            "data": {},
        }
    )

    # 로거의 error가 정확히 1번 호출되었는지 확인 (첫 번째 실패에 대한 로깅)
    assert logger.error.call_count == 1


@pytest.mark.asyncio
async def test_retry_ping_failure():
    # 웹소켓 모의 객체 생성
    websocket = AsyncMock(spec=WebSocket)
    websocket.send_json = AsyncMock(side_effect=Exception("연결 오류"))

    # 로거 모의 객체 생성
    logger = MagicMock(spec=logging.Logger)

    # 함수 실행 및 예외 확인
    with pytest.raises(WebSocketDisconnect):
        await retry_ping(websocket, logger)

    # 웹소켓의 send_json이 MAX_RETRIES 횟수만큼 호출되었는지 확인
    assert websocket.send_json.call_count == MAX_RETRIES
    # 로거의 error가 MAX_RETRIES 횟수만큼 호출되었는지 확인
    assert logger.error.call_count == MAX_RETRIES


# retry_pong 함수 테스트
@pytest.mark.asyncio
async def test_retry_pong_success():
    # 웹소켓 모의 객체 생성
    websocket = AsyncMock(spec=WebSocket)
    websocket.receive_json = AsyncMock(
        return_value={
            "type": "pong",
            "message": "",
            "data": {},
        }
    )

    # 로거 모의 객체 생성
    logger = MagicMock(spec=logging.Logger)

    # 함수 실행
    await retry_pong(websocket, logger)

    # 웹소켓의 receive_json이 호출되었는지 확인
    websocket.receive_json.assert_called_once()
    # 로거의 error가 호출되지 않았는지 확인
    logger.error.assert_not_called()


@pytest.mark.asyncio
async def test_retry_pong_success_on_second_try():
    # 웹소켓 모의 객체 생성
    websocket = AsyncMock(spec=WebSocket)

    # 첫 번째 호출에서는 유효하지 않은 응답을 반환하고, 두 번째 호출에서는 올바른 PONG 응답 반환
    websocket.receive_json = AsyncMock(
        side_effect=[
            {"type": "invalid"},
            {"type": "pong", "message": "", "data": {}},
        ]
    )

    # 로거 모의 객체 생성
    logger = MagicMock(spec=logging.Logger)

    # 함수 실행
    await retry_pong(websocket, logger)

    # 웹소켓의 receive_json이 정확히 2번 호출되었는지 확인
    assert websocket.receive_json.call_count == 2

    # 로거의 error가 정확히 1번 호출되었는지 확인 (첫 번째 실패에 대한 로깅)
    assert logger.error.call_count == 1

    # 로그 메시지에 "유효하지 않은 응답"이 포함되어 있는지 확인
    logger.error.assert_called_once()
    assert "유효하지 않은 응답" in logger.error.call_args[0][0]


@pytest.mark.asyncio
async def test_retry_pong_exception_then_success():
    # 웹소켓 모의 객체 생성
    websocket = AsyncMock(spec=WebSocket)

    # 첫 번째 호출에서는 예외 발생, 두 번째 호출에서는 올바른 PONG 응답 반환
    websocket.receive_json = AsyncMock(
        side_effect=[
            asyncio.TimeoutError(),
            {"type": "pong", "message": "", "data": {}},
        ]
    )

    # 로거 모의 객체 생성
    logger = MagicMock(spec=logging.Logger)

    # 함수 실행
    await retry_pong(websocket, logger)

    # 웹소켓의 receive_json이 정확히 2번 호출되었는지 확인
    assert websocket.receive_json.call_count == 2

    # 로거의 error가 정확히 1번 호출되었는지 확인 (첫 번째 시도 실패에 대한 로깅)
    assert logger.error.call_count == 1

    # 로그 메시지에 "오류 발생"이 포함되어 있는지 확인
    logger.error.assert_called_once()
    assert "오류 발생" in logger.error.call_args[0][0]


@pytest.mark.asyncio
async def test_retry_pong_invalid_response():
    # 웹소켓 모의 객체 생성
    websocket = AsyncMock(spec=WebSocket)
    websocket.receive_json = AsyncMock(return_value={"type": "invalid"})

    # 로거 모의 객체 생성
    logger = MagicMock(spec=logging.Logger)

    # 함수 실행 및 예외 확인
    with pytest.raises(WebSocketDisconnect):
        await retry_pong(websocket, logger, max_retries=1)

    # 웹소켓의 receive_json이 호출되었는지 확인
    websocket.receive_json.assert_called_once()
    # 로거의 error가 호출되었는지 확인
    logger.error.assert_called_once()


@pytest.mark.asyncio
async def test_retry_pong_timeout():
    # 웹소켓 모의 객체 생성
    websocket = AsyncMock(spec=WebSocket)
    websocket.receive_json = AsyncMock(side_effect=asyncio.TimeoutError())

    # 로거 모의 객체 생성
    logger = MagicMock(spec=logging.Logger)

    # 함수 실행
    with pytest.raises(WebSocketDisconnect):
        await retry_pong(websocket, logger, max_retries=1)

    # 웹소켓의 receive_json이 호출되었는지 확인
    websocket.receive_json.assert_called_once()
    # 로거의 error가 호출되었는지 확인
    logger.error.assert_called_once()


@pytest.mark.asyncio
async def test_retry_pong_exception():
    # 웹소켓 모의 객체 생성
    websocket = AsyncMock(spec=WebSocket)
    websocket.receive_json = AsyncMock(side_effect=Exception("테스트 예외"))

    # 로거 모의 객체 생성
    logger = MagicMock(spec=logging.Logger)

    # 함수 실행
    with pytest.raises(WebSocketDisconnect):
        await retry_pong(websocket, logger, max_retries=1)

    # 웹소켓의 receive_json이 호출되었는지 확인
    websocket.receive_json.assert_called_once()
    # 로거의 error가 호출되었는지 확인
    logger.error.assert_called_once()


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
