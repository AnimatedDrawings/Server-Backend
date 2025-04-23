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
        ad_animation=ad_animation,
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


# 새로 추가된 period_finish_render 함수 테스트
def test_period_finish_render():
    # 보상 광고 시간(20초) 이하일 때는 항상 False 반환
    assert not make_animation_feature.period_finish_render(timer=15, period=5)
    assert not make_animation_feature.period_finish_render(timer=20, period=5)

    # 보상 광고 시간 초과 & 주기에 맞을 때는 True 반환
    assert make_animation_feature.period_finish_render(timer=25, period=5)
    assert make_animation_feature.period_finish_render(timer=30, period=5)
    assert not make_animation_feature.period_finish_render(timer=26, period=5)

    # 다른 주기에 대한 테스트
    assert make_animation_feature.period_finish_render(timer=22, period=2)
    assert not make_animation_feature.period_finish_render(timer=23, period=2)


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
    - is_finish_render는 True를 반환하여 바로 렌더링 완료로 간주합니다.
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
        "ad_fast_api.domain.make_animation.sources.features.make_animation_feature.is_finish_render",
        new_callable=AsyncMock,
        return_value=True,
    ) as mock_is_finish_render, patch(
        "ad_fast_api.domain.make_animation.sources.features.make_animation_feature.cancel_render_async",
        new_callable=AsyncMock,
    ) as mock_cancel_render_async, patch(
        "ad_fast_api.domain.make_animation.sources.features.make_animation_feature.period_finish_render",
        return_value=True,
    ) as mock_period_finish_render, patch(
        "asyncio.sleep", new_callable=AsyncMock
    ) as mock_sleep, patch(
        "pathlib.Path.exists", return_value=True
    ) as mock_exists:
        await make_animation_feature.check_connection_and_rendering(
            job_id=job_id,
            base_path=base_path,
            relative_video_file_path=relative_video_file_path,
            websocket=websocket,
            logger=logger,
        )

        # check_connection이 호출되었는지 확인
        mock_check_connection.assert_called_with(
            timer=0,
            period=5,
            websocket=websocket,
            logger=logger,
        )
        # period_finish_render가 호출되었는지 확인
        mock_period_finish_render.assert_called_once()
        # is_finish_render가 호출되었는지 확인
        mock_is_finish_render.assert_called_once_with(
            job_id=job_id,
            logger=logger,
            timeout_seconds=7,
        )
        # 렌더링 완료 메시지가 로깅되었는지 확인
        logger.info.assert_called_once()
        # 렌더링 완료이므로 cancel_render_async는 호출되지 않아야 함
        mock_cancel_render_async.assert_not_called()


@pytest.mark.asyncio
async def test_check_connection_and_rendering_file_not_exists():
    """
    렌더링은 완료되었지만 파일이 존재하지 않는 경우를 테스트합니다.
    """
    job_id = "job_completed_no_file"
    base_path = Path("/dummy/path")
    relative_video_file_path = Path("dummy.gif")
    websocket = DummyWebSocket()
    logger = MagicMock()

    with patch(
        "ad_fast_api.domain.make_animation.sources.features.make_animation_feature.check_connection",
        new_callable=AsyncMock,
    ) as mock_check_connection, patch(
        "ad_fast_api.domain.make_animation.sources.features.make_animation_feature.is_finish_render",
        new_callable=AsyncMock,
        return_value=True,
    ) as mock_is_finish_render, patch(
        "ad_fast_api.domain.make_animation.sources.features.make_animation_feature.cancel_render_async",
        new_callable=AsyncMock,
    ) as mock_cancel_render_async, patch(
        "ad_fast_api.domain.make_animation.sources.features.make_animation_feature.period_finish_render",
        return_value=True,
    ) as mock_period_finish_render, patch(
        "asyncio.sleep", new_callable=AsyncMock
    ) as mock_sleep, patch(
        "pathlib.Path.exists", return_value=False
    ) as mock_exists:
        with pytest.raises(Exception) as exc_info:
            await make_animation_feature.check_connection_and_rendering(
                job_id=job_id,
                base_path=base_path,
                relative_video_file_path=relative_video_file_path,
                websocket=websocket,
                logger=logger,
            )

        assert (
            "Rendering has been completed, but the video file does not exist."
            in str(exc_info.value)
        )
        logger.error.assert_called_once()
        mock_cancel_render_async.assert_not_called()


@pytest.mark.asyncio
async def test_check_connection_and_rendering_timeout():
    """
    렌더링이 완료되지 않아 타임아웃되는 경우를 테스트합니다.
    최대 대기 시간 후 타임아웃 예외가 발생해야 합니다.
    """
    job_id = "job_timeout"
    base_path = Path("/dummy/path")
    relative_video_file_path = Path("dummy.gif")
    websocket = DummyWebSocket()
    logger = MagicMock()

    # check_connection 함수는 정상 동작, render_timer가 최대값을 초과하도록 설정
    with patch(
        "ad_fast_api.domain.make_animation.sources.features.make_animation_feature.check_connection",
        new_callable=AsyncMock,
    ) as mock_check_connection, patch(
        "ad_fast_api.domain.make_animation.sources.features.make_animation_feature.is_finish_render",
        new_callable=AsyncMock,
        return_value=False,
    ) as mock_is_finish_render, patch(
        "ad_fast_api.domain.make_animation.sources.features.make_animation_feature.cancel_render_async",
        new_callable=AsyncMock,
    ) as mock_cancel_render_async, patch(
        "ad_fast_api.domain.make_animation.sources.features.make_animation_feature.period_finish_render",
        return_value=False,  # period_finish_render는 항상 False 반환
    ) as mock_period_finish_render, patch(
        "asyncio.sleep",
        new_callable=AsyncMock,
        side_effect=lambda x: setattr(
            make_animation_feature, "_test_render_timer", 180
        ),
    ) as mock_sleep:
        make_animation_feature._test_render_timer = 0  # type: ignore # 테스트용 타이머 초기화

        # render_timer 값을 조작해서 max_render_time을 초과하도록 함
        def increment_timer(*args, **kwargs):
            nonlocal render_timer
            render_timer += 1
            return False

        render_timer = 180  # 최대 시간(180초) 설정

        with pytest.raises(Exception) as exc_info:
            await make_animation_feature.check_connection_and_rendering(
                job_id=job_id,
                base_path=base_path,
                relative_video_file_path=relative_video_file_path,
                websocket=websocket,
                logger=logger,
            )

        assert "Rendering time has exceeded the limit." in str(exc_info.value)
        mock_cancel_render_async.assert_called_once_with(job_id=job_id, logger=logger)
        logger.error.assert_called_once()


@pytest.mark.asyncio
async def test_check_connection_and_rendering_websocket_disconnect():
    """
    check_connection 호출 시 WebSocketDisconnect 예외가 발생하는 경우를 테스트합니다.
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
        assert "The websocket connection with the client has been terminated" in str(
            exc_info.value
        )
        mock_cancel_render_async.assert_called_once_with(job_id=job_id, logger=logger)
        logger.error.assert_called_once()


@pytest.mark.asyncio
async def test_check_connection_and_rendering_other_exception():
    """
    check_connection 호출 중 기타 예외가 발생하는 경우를 테스트합니다.
    """
    job_id = "job_other_exception"
    base_path = Path("/dummy/path")
    relative_video_file_path = Path("dummy.gif")
    websocket = DummyWebSocket()
    logger = MagicMock()

    with patch(
        "ad_fast_api.domain.make_animation.sources.features.make_animation_feature.check_connection",
        new_callable=AsyncMock,
        side_effect=Exception("Unexpected error"),
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
        assert "An error occurred while processing the job" in str(exc_info.value)
        mock_cancel_render_async.assert_called_once_with(job_id=job_id, logger=logger)
        logger.error.assert_called_once()
