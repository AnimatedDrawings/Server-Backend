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
            Path("/dummy/path"),
            logger,
            timeout_seconds=1,
        )
        assert result["type"] == WebSocketType.ERROR


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
            Path("/dummy/path"),
            logger,
            timeout_seconds=1,
        )
        assert result["type"] == WebSocketType.RUNNING
        assert result["data"]["job_id"] == "job123"  # type: ignore


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
            Path("/dummy/path"),
            logger,
            timeout_seconds=1,
        )
        assert result["type"] == WebSocketType.FULL_JOB


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
            Path("/dummy/path"),
            logger,
            timeout_seconds=1,
        )
        assert result["type"] == WebSocketType.ERROR


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
            Path("/dummy/path"),
            logger,
            timeout_seconds=1,
        )
        assert result["type"] == WebSocketType.ERROR


@pytest.mark.asyncio
async def test_cancel_render_none_response():
    """
    응답이 None인 경우, cancel_render_async가 오류를 로깅하고 None을 반환하는지 확인합니다.
    """
    dummy_client = AsyncMock()
    dummy_client.call.return_value = None

    with patch.object(img_anim, "get_zero_client", return_value=dummy_client):
        logger = logging.getLogger("test_cancel_render_none_response")
        result = await img_anim.cancel_render_async(
            "job123",
            logger,
            timeout_seconds=1,
        )
        assert result is None


@pytest.mark.asyncio
async def test_cancel_render_terminate():
    """
    응답 타입이 TERMINATE인 경우, 정상적으로 취소 처리되는지 확인합니다.
    """
    dummy_client = AsyncMock()
    dummy_client.call.return_value = {"type": "terminate"}

    with patch.object(img_anim, "get_zero_client", return_value=dummy_client):
        logger = logging.getLogger("test_cancel_render_terminate")
        result = await img_anim.cancel_render_async(
            "job123",
            logger,
            timeout_seconds=1,
        )
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
        result = await img_anim.cancel_render_async(
            "job123",
            logger,
            timeout_seconds=1,
        )
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
        result = await img_anim.cancel_render_async(
            "job123",
            logger,
            timeout_seconds=1,
        )
        assert result is None


@pytest.mark.asyncio
async def test_is_finish_render_finished():
    """
    is_finish_render 함수가 'TERMINATE' 응답인 경우 True를 반환하는지 확인합니다.
    """
    dummy_client = AsyncMock()
    dummy_client.call.return_value = {"type": "TERMINATE"}

    with patch.object(img_anim, "get_zero_client", return_value=dummy_client):
        logger = logging.getLogger("test_is_finish_render_finished")
        result = await img_anim.is_finish_render("job123", logger, timeout_seconds=1)
        assert result is True


@pytest.mark.asyncio
async def test_is_finish_render_running():
    """
    is_finish_render 함수가 'RUNNING' 응답인 경우 False를 반환하는지 확인합니다.
    """
    dummy_client = AsyncMock()
    dummy_client.call.return_value = {"type": "RUNNING"}

    with patch.object(img_anim, "get_zero_client", return_value=dummy_client):
        logger = logging.getLogger("test_is_finish_render_running")
        result = await img_anim.is_finish_render("job123", logger, timeout_seconds=1)
        assert result is False


@pytest.mark.asyncio
async def test_is_finish_render_none_response():
    """
    is_finish_render 함수가 None 응답인 경우, 예외를 발생시키는지 확인합니다.
    """
    dummy_client = AsyncMock()
    dummy_client.call.return_value = None

    with patch.object(img_anim, "get_zero_client", return_value=dummy_client):
        logger = logging.getLogger("test_is_finish_render_none_response")
        with pytest.raises(Exception) as excinfo:
            await img_anim.is_finish_render("job123", logger, timeout_seconds=1)
        assert "no return value" in str(excinfo.value)


@pytest.mark.asyncio
async def test_is_finish_render_unknown_response():
    """
    is_finish_render 함수가 알 수 없는 type의 응답인 경우, 예외를 발생시키는지 확인합니다.
    """
    dummy_client = AsyncMock()
    dummy_client.call.return_value = {"type": "UNKNOWN_TYPE"}

    with patch.object(img_anim, "get_zero_client", return_value=dummy_client):
        logger = logging.getLogger("test_is_finish_render_unknown_response")
        with pytest.raises(Exception) as excinfo:
            await img_anim.is_finish_render("job123", logger, timeout_seconds=1)
        assert "unknown" in str(excinfo.value)


@pytest.mark.asyncio
async def test_is_finish_render_exception():
    """
    is_finish_render 함수 호출 중 예외가 발생할 경우, 해당 예외가 전달되는지 확인합니다.
    """
    dummy_client = AsyncMock()
    dummy_client.call.side_effect = Exception("Test exception")

    with patch.object(img_anim, "get_zero_client", return_value=dummy_client):
        logger = logging.getLogger("test_is_finish_render_exception")
        with pytest.raises(Exception) as excinfo:
            await img_anim.is_finish_render("job123", logger, timeout_seconds=1)
        assert "Test exception" in str(excinfo.value)
