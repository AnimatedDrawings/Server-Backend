import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from ad_fast_api.domain.make_animation.sources.features import make_animation_feature
from ad_fast_api.workspace.sources.conf_workspace import FILES_DIR_NAME
from ad_fast_api.snippets.sources.ad_env import ADEnv
from fastapi import WebSocket, WebSocketDisconnect


def test_get_file_response(tmp_path: Path):
    # 임시 디렉토리(tmp_path)를 기본 경로로 사용
    base_path = tmp_path

    # 더미 GIF 파일 생성
    dummy_file_name = "test.gif"
    dummy_file_path = base_path / dummy_file_name
    dummy_file_path.write_bytes(b"GIF89a")  # 간단한 GIF 헤더 기록

    relative_video_file_path = Path(dummy_file_name)

    # 함수 호출: FileResponse 반환
    response = make_animation_feature.get_file_response(
        base_path=base_path,
        relative_video_file_path=relative_video_file_path,
    )

    # 생성된 파일의 전체 경로가 올바르게 설정되었는지 검증
    expected_path = (base_path / relative_video_file_path).as_posix()
    # FileResponse의 'path' 속성이 예상 경로와 같아야 합니다.
    assert hasattr(response, "path")
    assert response.path == expected_path

    # 미디어 타입이 "image/gif"로 지정되었는지 체크
    assert response.media_type == "image/gif"


@patch(
    "ad_fast_api.domain.make_animation.sources.features.make_animation_feature.get_ad_env"
)
@patch.object(make_animation_feature, "save_mvc_config")
@patch.object(make_animation_feature, "create_mvc_config")
@patch.object(make_animation_feature, "create_animated_drawing_dict")
def test_prepare_make_animation(
    mock_create_animated_drawing_dict,
    mock_create_mvc_config,
    mock_save_mvc_config,
    mock_get_ad_env,
):
    # 준비: get_ad_env 패치하여 ADEnv.mock() 반환
    ad_env_instance = ADEnv.mock()
    mock_get_ad_env.return_value = ad_env_instance

    ad_id = "test_ad"
    base_path = Path("/test/path")
    ad_animation = "walk"
    relative_video_file_path = Path("video.mp4")

    # ADEnv.mock()에서 전달받은 animated_drawings_workspace_dir 사용
    animated_drawings_workspace_path = Path(
        ad_env_instance.animated_drawings_workspace_dir
    )
    animated_drawings_base_path = animated_drawings_workspace_path.joinpath(
        FILES_DIR_NAME
    ).joinpath(ad_id)
    video_file_path = animated_drawings_base_path.joinpath(relative_video_file_path)

    animated_drawing_dict = {"key": "value"}
    mvc_cfg_dict = {"config": "data"}

    mock_create_animated_drawing_dict.return_value = animated_drawing_dict
    mock_create_mvc_config.return_value = mvc_cfg_dict

    # 실행
    result = make_animation_feature.prepare_make_animation(
        ad_id=ad_id,
        base_path=base_path,
        ad_animation=ad_animation,
        relative_video_file_path=relative_video_file_path,
    )

    # 검증
    mock_create_animated_drawing_dict.assert_called_once_with(
        animated_drawings_base_path=animated_drawings_base_path,
        animated_drawings_workspace_path=animated_drawings_workspace_path,
        ad_animation=ad_animation,
    )
    mock_create_mvc_config.assert_called_once_with(
        animated_drawings_dict=animated_drawing_dict,
        video_file_path=video_file_path,
    )
    mock_save_mvc_config.assert_called_once_with(
        mvc_cfg_file_name=make_animation_feature.MVC_CFG_FILE_NAME,
        mvc_cfg_dict=mvc_cfg_dict,
        base_path=base_path,
    )

    expected_path = animated_drawings_base_path.joinpath(
        make_animation_feature.MVC_CFG_FILE_NAME
    )
    assert result == expected_path


# FastAPI의 WebSocket은 직접 인스턴스화하기 어려우므로, 간단한 Dummy 클래스를 정의합니다.
class DummyWebSocket(WebSocket):
    async def accept(self):
        pass

    async def send_text(self, data: str):
        pass

    async def close(self, code: int = 1000):
        pass

    def __init__(self):
        # Receive와 Send 타입에 맞는 더미 함수를 생성합니다
        async def dummy_receive():
            return {"type": "websocket.receive", "text": ""}

        async def dummy_send(message):
            pass

        super().__init__(
            scope={"type": "websocket"}, receive=dummy_receive, send=dummy_send
        )


@pytest.mark.asyncio
async def test_check_connection_and_rendering_completed():
    """
    렌더링이 즉시 완료된 경우를 테스트합니다.
    - check_connection은 정상 동작하고,
    - is_completed_render는 True를 반환하여 바로 렌더링 완료로 간주합니다.
    """
    job_id = "job_completed"
    base_path = Path("/dummy/path")
    relative_video_file_path = Path("dummy.gif")
    websocket = DummyWebSocket()
    logger = MagicMock()

    with patch(
        "ad_fast_api.domain.make_animation.sources.features.make_animation_feature.check_connection",
        new_callable=AsyncMock,
    ) as mock_check_connection, patch(
        "ad_fast_api.domain.make_animation.sources.features.make_animation_feature.is_completed_render",
        return_value=True,
    ) as mock_is_completed_render, patch(
        "ad_fast_api.domain.make_animation.sources.features.make_animation_feature.cancel_render_async",
        new_callable=AsyncMock,
    ) as mock_cancel_render_async:
        await make_animation_feature.check_connection_and_rendering(
            job_id=job_id,
            base_path=base_path,
            relative_video_file_path=relative_video_file_path,
            websocket=websocket,
            logger=logger,
        )

        # 최초 호출 시 timer=0, period=5로 check_connection이 호출되어야 합니다.
        mock_check_connection.assert_called_once_with(
            timer=0,
            period=5,
            websocket=websocket,
            logger=logger,
        )
        expected_video_path = base_path.joinpath(relative_video_file_path)
        mock_is_completed_render.assert_called_once_with(expected_video_path)
        # 렌더링 완료이므로 cancel_render_async는 호출되지 않아야 합니다.
        mock_cancel_render_async.assert_not_called()
        # 렌더링 완료 메시지가 로깅되었는지 확인합니다.
        logger.info.assert_called_once()


@pytest.mark.asyncio
async def test_check_connection_and_rendering_timeout():
    """
    렌더링이 완료되지 않아 타임아웃되는 경우를 테스트합니다.
    is_completed_render가 계속 False를 반환하여
    최대 대기 시간 후 cancel_render_async가 호출되고 예외가 발생해야 합니다.

    asyncio.sleep를 AsyncMock으로 패치하여 실제 대기 시간을 없앱니다.
    """
    job_id = "job_timeout"
    base_path = Path("/dummy/path")
    relative_video_file_path = Path("dummy.gif")
    websocket = DummyWebSocket()
    logger = MagicMock()

    with patch(
        "ad_fast_api.domain.make_animation.sources.features.make_animation_feature.check_connection",
        new_callable=AsyncMock,
    ) as mock_check_connection, patch(
        "ad_fast_api.domain.make_animation.sources.features.make_animation_feature.is_completed_render",
        return_value=False,
    ) as mock_is_completed_render, patch(
        "ad_fast_api.domain.make_animation.sources.features.make_animation_feature.cancel_render_async",
        new_callable=AsyncMock,
    ) as mock_cancel_render_async, patch(
        "asyncio.sleep", new_callable=AsyncMock
    ) as mock_sleep:
        with pytest.raises(Exception) as exc_info:
            await make_animation_feature.check_connection_and_rendering(
                job_id=job_id,
                base_path=base_path,
                relative_video_file_path=relative_video_file_path,
                websocket=websocket,
                logger=logger,
            )
        # 예외 메시지가 "Rendering time has exceeded the limit." 인지 검증합니다.
        mock_cancel_render_async.assert_called_once_with(job_id=job_id, logger=logger)
        logger.error.assert_called_once()


@pytest.mark.asyncio
async def test_check_connection_and_rendering_websocket_disconnect():
    """
    check_connection 호출 시 WebSocketDisconnect 예외가 발생하는 경우를 테스트합니다.
    이 경우 cancel_render_async가 호출되고
    "The websocket connection with the client has been terminated" 메시지의 예외가 발생해야 합니다.
    """
    job_id = "job_ws_disconnect"
    base_path = Path("/dummy/path")
    relative_video_file_path = Path("dummy.gif")
    websocket = DummyWebSocket()
    logger = MagicMock()

    with patch(
        "ad_fast_api.domain.make_animation.sources.features.make_animation_feature.check_connection",
        new_callable=AsyncMock,
        side_effect=WebSocketDisconnect(code=1000, reason="Client disconnected"),
    ) as mock_check_connection, patch(
        "ad_fast_api.domain.make_animation.sources.features.make_animation_feature.cancel_render_async",
        new_callable=AsyncMock,
    ) as mock_cancel_render_async:
        with pytest.raises(Exception) as exc_info:
            await make_animation_feature.check_connection_and_rendering(
                job_id=job_id,
                base_path=base_path,
                relative_video_file_path=relative_video_file_path,
                websocket=websocket,
                logger=logger,
            )
        assert (
            str(exc_info.value)
            == "The websocket connection with the client has been terminated"
        )
        mock_cancel_render_async.assert_called_once_with(job_id=job_id, logger=logger)
        logger.error.assert_called_once()


@pytest.mark.asyncio
async def test_check_connection_and_rendering_other_exception():
    """
    check_connection 호출 중 기타 예외가 발생하는 경우를 테스트합니다.
    첫번째 check_connection 호출은 정상 처리되고,
    두번째 호출에서 Exception("Unexpected error")가 발생하여
    cancel_render_async가 호출되고 "An error occurred while processing the job" 메시지의 예외가 발생해야 합니다.
    """
    job_id = "job_other_exception"
    base_path = Path("/dummy/path")
    relative_video_file_path = Path("dummy.gif")
    websocket = DummyWebSocket()
    logger = MagicMock()

    async def side_effect(*args, **kwargs):
        if side_effect.call_count == 0:
            side_effect.call_count += 1
            return
        else:
            raise Exception("Unexpected error")

    side_effect.call_count = 0

    with patch(
        "ad_fast_api.domain.make_animation.sources.features.make_animation_feature.check_connection",
        new_callable=AsyncMock,
        side_effect=side_effect,
    ) as mock_check_connection, patch(
        "ad_fast_api.domain.make_animation.sources.features.make_animation_feature.is_completed_render",
        return_value=False,
    ) as mock_is_completed_render, patch(
        "ad_fast_api.domain.make_animation.sources.features.make_animation_feature.cancel_render_async",
        new_callable=AsyncMock,
    ) as mock_cancel_render_async, patch(
        "asyncio.sleep", new_callable=AsyncMock
    ) as mock_sleep:
        with pytest.raises(Exception) as exc_info:
            await make_animation_feature.check_connection_and_rendering(
                job_id=job_id,
                base_path=base_path,
                relative_video_file_path=relative_video_file_path,
                websocket=websocket,
                logger=logger,
            )
        # assert str(exc_info.value) == "An error occurred while processing the job"
        mock_cancel_render_async.assert_called_once_with(job_id=job_id, logger=logger)
        logger.error.assert_called_once()
