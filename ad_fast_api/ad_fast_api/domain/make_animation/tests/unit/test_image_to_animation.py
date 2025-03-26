import logging
from pathlib import Path
from unittest.mock import AsyncMock, patch
import pytest
from ad_fast_api.domain.make_animation.sources.features import (
    image_to_animation as img_anim,
)
from ad_fast_api.domain.make_animation.sources.make_animation_schema import (
    WebSocketType,
)

# --- start_render_async 함수 테스트 ---


@pytest.mark.asyncio
async def test_start_render_none_response():
    """
    응답이 None인 경우, 오류 메시지를 반환하는지 확인합니다.
    """
    dummy_client = AsyncMock()
    dummy_client.call.return_value = None

    with patch.object(img_anim, "get_zero_client", return_value=dummy_client):
        logger = logging.getLogger("test_start_render_none_response")
        result = await img_anim.start_render_async(
            Path("/dummy/path"), logger, timeout=1000
        )
        assert result["type"] == WebSocketType.ERROR.value
        assert "no return value" in result["message"]


@pytest.mark.asyncio
async def test_start_render_running():
    """
    응답 타입이 RUNNING이고 job_id가 포함된 경우 올바른 메시지를 반환하는지 확인합니다.
    """
    dummy_client = AsyncMock()
    dummy_client.call.return_value = {
        "type": WebSocketType.RUNNING.value,
        "data": {"job_id": "job123"},
    }

    with patch.object(img_anim, "get_zero_client", return_value=dummy_client):
        logger = logging.getLogger("test_start_render_running")
        result = await img_anim.start_render_async(
            Path("/dummy/path"), logger, timeout=1000
        )
        assert result["type"] == WebSocketType.RUNNING.value
        assert result["message"] == "Animation rendering started."
        assert result["data"]["job_id"] == "job123"


@pytest.mark.asyncio
async def test_start_render_fulljob():
    """
    응답 타입이 FULL_JOB인 경우, 작업량이 많다는 메시지를 올바르게 반환하는지 확인합니다.
    """
    dummy_client = AsyncMock()
    dummy_client.call.return_value = {"type": WebSocketType.FULL_JOB.value}

    with patch.object(img_anim, "get_zero_client", return_value=dummy_client):
        logger = logging.getLogger("test_start_render_fulljob")
        result = await img_anim.start_render_async(
            Path("/dummy/path"), logger, timeout=1000
        )
        assert result["type"] == WebSocketType.FULL_JOB.value
        assert "high" in result["message"]


@pytest.mark.asyncio
async def test_start_render_unknown_type():
    """
    알 수 없는 타입의 응답일 경우, 오류 메시지(unknown return value)가 반환되는지 확인합니다.
    """
    dummy_client = AsyncMock()
    dummy_client.call.return_value = {"type": "unknown", "data": {}}

    with patch.object(img_anim, "get_zero_client", return_value=dummy_client):
        logger = logging.getLogger("test_start_render_unknown_type")
        result = await img_anim.start_render_async(
            Path("/dummy/path"), logger, timeout=1000
        )
        assert result["type"] == WebSocketType.ERROR.value
        assert "unknown return value" in result["message"]


@pytest.mark.asyncio
async def test_start_render_exception():
    """
    호출 중 예외가 발생하는 경우, 해당 예외 메시지를 포함한 오류 메시지가 반환되는지 확인합니다.
    """
    dummy_client = AsyncMock()
    dummy_client.call.side_effect = Exception("Test exception")

    with patch.object(img_anim, "get_zero_client", return_value=dummy_client):
        logger = logging.getLogger("test_start_render_exception")
        result = await img_anim.start_render_async(
            Path("/dummy/path"), logger, timeout=1000
        )
        assert result["type"] == WebSocketType.ERROR.value
        assert "Test exception" in result["message"]


# --- cancel_render_async 함수 테스트 ---


@pytest.mark.asyncio
async def test_cancel_render_none_response():
    """
    응답이 None인 경우, cancel_render_async가 오류를 로깅하고 None을 반환하는지 확인합니다.
    """
    dummy_client = AsyncMock()
    dummy_client.call.return_value = None

    with patch.object(img_anim, "get_zero_client", return_value=dummy_client):
        logger = logging.getLogger("test_cancel_render_none_response")
        result = await img_anim.cancel_render_async("job123", logger, timeout=1000)
        assert result is None


@pytest.mark.asyncio
async def test_cancel_render_terminate():
    """
    응답 타입이 TERMINATE인 경우, 정상적으로 취소 처리되는지 확인합니다.
    """
    dummy_client = AsyncMock()
    dummy_client.call.return_value = {"type": WebSocketType.TERMINATE.value}

    with patch.object(img_anim, "get_zero_client", return_value=dummy_client):
        logger = logging.getLogger("test_cancel_render_terminate")
        result = await img_anim.cancel_render_async("job123", logger, timeout=1000)
        assert result is None


@pytest.mark.asyncio
async def test_cancel_render_unknown():
    """
    알 수 없는 타입의 응답인 경우, 오류가 로깅되고 None이 반환되는지 확인합니다.
    """
    dummy_client = AsyncMock()
    dummy_client.call.return_value = {"type": "unknown"}

    with patch.object(img_anim, "get_zero_client", return_value=dummy_client):
        logger = logging.getLogger("test_cancel_render_unknown")
        result = await img_anim.cancel_render_async("job123", logger, timeout=1000)
        assert result is None


@pytest.mark.asyncio
async def test_cancel_render_exception():
    """
    호출 중 예외가 발생하는 경우, 오류를 로깅하고 None을 반환하는지 확인합니다.
    """
    dummy_client = AsyncMock()
    dummy_client.call.side_effect = Exception("Cancel exception")

    with patch.object(img_anim, "get_zero_client", return_value=dummy_client):
        logger = logging.getLogger("test_cancel_render_exception")
        result = await img_anim.cancel_render_async("job123", logger, timeout=1000)
        assert result is None


# --- is_completed_render 함수 테스트 ---


def test_is_completed_render(tmp_path):
    """
    파일이 존재할 경우 True, 존재하지 않으면 False를 반환하는지 확인합니다.
    """
    # 파일이 존재하는 경우
    file_path = tmp_path / "video.mp4"
    file_path.write_text("dummy content")
    assert img_anim.is_completed_render(file_path) is True

    # 파일이 존재하지 않는 경우
    non_existent = tmp_path / "nonexistent.mp4"
    assert img_anim.is_completed_render(non_existent) is False
