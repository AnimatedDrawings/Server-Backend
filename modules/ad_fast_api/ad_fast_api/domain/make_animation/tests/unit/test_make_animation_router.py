import logging
import pytest
from fastapi import FastAPI, WebSocketDisconnect
from fastapi.testclient import TestClient
from fastapi.responses import Response, FileResponse
from ad_fast_api.domain.make_animation.sources.make_animation_schema import (
    WebSocketType,
)

# 모듈 임포트
import ad_fast_api.domain.make_animation.sources.make_animation_router as router_module

# 테스트를 위한 FastAPI 앱 생성 및 라우터 포함
app = FastAPI()
app.include_router(router_module.router)
client = TestClient(app)


# FakePath 클래스를 생성하여 Path 객체를 모방합니다.
class FakePath:
    def __init__(self, exists, path="fake/file/path"):
        self._exists = exists
        self.path = path

    def exists(self):
        return self._exists

    def __str__(self):
        return self.path

    def stat(self):
        # 파일 크기를 모의하는 객체 반환
        class FakeStat:
            def __init__(self):
                self.st_size = 1024  # 가상의 파일 크기

        return FakeStat()


# /download_animation 엔드포인트 테스트 - 파일이 존재하는 경우
def test_download_animation_file_exists(monkeypatch):
    fake_video_path = FakePath(True, "fake/full/path.mp4")
    fake_relative_path = "fake/relative/path.mp4"

    def fake_get_video_file_path(base_path, ad_animation, logger):
        return fake_video_path, fake_relative_path

    def fake_get_file_response(base_path, relative_video_file_path):
        # 더미 파일 응답 반환
        return Response(content="dummy file content", media_type="image/gif")

    monkeypatch.setattr(router_module, "get_video_file_path", fake_get_video_file_path)
    monkeypatch.setattr(router_module, "get_file_response", fake_get_file_response)
    monkeypatch.setattr(router_module, "get_base_path", lambda ad_id: "dummy_base_path")
    monkeypatch.setattr(
        router_module,
        "setup_logger",
        lambda ad_id, level=logging.DEBUG: logging.getLogger("dummy_logger"),
    )

    response = client.get(
        "/download_animation", params={"ad_id": "123", "ad_animation": "test"}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/gif"
    assert response.text == "dummy file content"


# /download_animation 엔드포인트 테스트 - 파일이 존재하지 않는 경우
def test_download_animation_file_not_exists(monkeypatch):
    fake_video_path = FakePath(False, "fake/full/path.mp4")
    fake_relative_path = "fake/relative/path.mp4"

    def fake_get_video_file_path(base_path, ad_animation, logger):
        return fake_video_path, fake_relative_path

    monkeypatch.setattr(router_module, "get_video_file_path", fake_get_video_file_path)
    monkeypatch.setattr(router_module, "get_base_path", lambda ad_id: "dummy_base_path")
    monkeypatch.setattr(
        router_module,
        "setup_logger",
        lambda ad_id, level=logging.DEBUG: logging.getLogger("dummy_logger"),
    )

    response = client.get(
        "/download_animation", params={"ad_id": "123", "ad_animation": "test"}
    )
    # 파일이 존재하지 않으므로 NOT_FOUND_ANIMATION_FILE 예외가 발생하여 500 에러를 반환할 수 있습니다.
    assert response.status_code == 500


# /make_animation 웹소켓 엔드포인트 테스트 - 파일이 이미 존재하는 경우
def test_make_animation_websocket_file_exists(monkeypatch):
    fake_video_path = FakePath(True, "fake/full/path.mp4")
    fake_relative_path = "fake/relative/path.mp4"

    def fake_get_video_file_path(base_path, ad_animation, logger):
        return fake_video_path, fake_relative_path

    monkeypatch.setattr(router_module, "get_video_file_path", fake_get_video_file_path)
    monkeypatch.setattr(router_module, "get_base_path", lambda ad_id: "dummy_base_path")
    monkeypatch.setattr(
        router_module,
        "setup_logger",
        lambda ad_id, level=logging.DEBUG: logging.getLogger("dummy_logger"),
    )
    # check_available_animation이 예외를 발생하지 않도록 패치합니다.
    monkeypatch.setattr(
        router_module, "check_available_animation", lambda ad_animation, logger: None
    )

    with client.websocket_connect(
        "/make_animation?ad_id=123&ad_animation=test"
    ) as websocket:
        data = websocket.receive_json()
        # 파일이 이미 존재하므로 COMPLETE 메시지를 바로 받아야 합니다.
        # lower/upper 무시 비교 처리
        assert data["type"] == WebSocketType.COMPLETE.value
        assert data["data"]["file_path"] == fake_relative_path


# /make_animation 웹소켓 엔드포인트 테스트 - 파일이 존재하지 않아 렌더링 프로세스 진행하는 경우
def test_make_animation_websocket_file_not_exists(monkeypatch):
    fake_video_path = FakePath(False, "fake/full/path.mp4")
    fake_relative_path = "fake/relative/path.mp4"

    def fake_get_video_file_path(base_path, ad_animation, logger):
        return fake_video_path, fake_relative_path

    monkeypatch.setattr(router_module, "get_video_file_path", fake_get_video_file_path)
    monkeypatch.setattr(router_module, "get_base_path", lambda ad_id: "dummy_base_path")
    monkeypatch.setattr(
        router_module,
        "setup_logger",
        lambda ad_id, level=logging.DEBUG: logging.getLogger("dummy_logger"),
    )

    # check_available_animation를 통과하도록 패치합니다.
    monkeypatch.setattr(
        router_module, "check_available_animation", lambda ad_animation, logger: None
    )

    # 애니메이션 렌더링 준비를 위한 더미 구성 파일 경로 반환
    monkeypatch.setattr(
        router_module,
        "prepare_make_animation",
        lambda ad_id, base_path, ad_animation, relative_video_file_path: "dummy_cfg_path.yaml",
    )

    # 렌더링 시작 요청을 모방하는 비동기 함수
    async def fake_start_render_async(animated_drawings_mvc_cfg_path, logger):
        return {"type": "RUNNING", "data": {"job_id": "12345"}}

    monkeypatch.setattr(router_module, "start_render_async", fake_start_render_async)

    # 렌더링 진행 체크 함수를 모방 (짧은 지연을 추가 및 COMPLETE 메시지 전송)
    async def fake_check_connection_and_rendering(
        job_id, base_path, relative_video_file_path, websocket, logger
    ):
        import asyncio

        await asyncio.sleep(0.1)  # COMPLETE 메시지가 전송될 시간을 확보하기 위한 지연
        await websocket.send_json(
            {"type": "COMPLETE", "data": {"file_path": relative_video_file_path}}
        )

    monkeypatch.setattr(
        router_module,
        "check_connection_and_rendering",
        fake_check_connection_and_rendering,
    )

    with client.websocket_connect(
        "/make_animation?ad_id=123&ad_animation=test"
    ) as websocket:
        # 첫 번째 메시지는 RUNNING 타입이어야 합니다.
        first_message = websocket.receive_json()
        assert first_message["type"] == WebSocketType.RUNNING
        assert first_message["data"]["job_id"] == "12345"
        # 두 번째 메시지는 COMPLETE 타입이어야 합니다.
        second_message = websocket.receive_json()
        assert second_message["type"] == WebSocketType.COMPLETE
        assert second_message["data"]["file_path"] == fake_relative_path


# /make_animation 웹소켓 엔드포인트 테스트 - 유효하지 않은 애니메이션 이름인 경우
def test_make_animation_websocket_invalid_animation(monkeypatch):
    # check_available_animation이 예외를 발생하도록 패치합니다.
    def fake_check_available_animation(ad_animation, logger):
        raise Exception("유효하지 않은 애니메이션")

    monkeypatch.setattr(
        router_module, "check_available_animation", fake_check_available_animation
    )
    monkeypatch.setattr(router_module, "get_base_path", lambda ad_id: "dummy_base_path")
    monkeypatch.setattr(
        router_module,
        "setup_logger",
        lambda ad_id, level=logging.DEBUG: logging.getLogger("dummy_logger"),
    )

    with client.websocket_connect(
        "/make_animation?ad_id=123&ad_animation=invalid"
    ) as websocket:
        error_message = websocket.receive_json()
        assert error_message["type"] == "ERROR"
        assert "유효하지 않은 애니메이션" in error_message["message"]
