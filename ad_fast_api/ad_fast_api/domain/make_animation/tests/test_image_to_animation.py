import pytest
from pathlib import Path
from unittest.mock import patch, AsyncMock
from ad_fast_api.domain.make_animation.sources.features import image_to_animation


@pytest.mark.asyncio
async def test_render_start_async_no_status():
    """
    Test that when the response is None or missing the 'status' key,
    the function raises an Exception with a message indicating failure.
    """
    mvc_cfg_path = Path("/test/path/config.json")
    # 응답이 None 인 경우: "status" 키조차 존재하지 않음.
    expected_response = None

    with patch.object(
        image_to_animation.AsyncZeroClient,
        "call",
        new_callable=AsyncMock,
    ) as mock_call:
        mock_call.return_value = expected_response

        with pytest.raises(Exception) as exc_info:
            await image_to_animation.render_start_async(mvc_cfg_path)

        assert "애니메이션 렌더링에 실패" in str(exc_info.value)


@pytest.mark.asyncio
async def test_image_to_animation_async_failure():
    """
    Test that when the response contains 'status' equal to 'fail',
    the function raises an Exception with the error message from the response.
    """
    mvc_cfg_path = Path("/test/path/config.json")
    expected_response = {"status": "fail", "message": "failure occurred"}

    with patch.object(
        image_to_animation.AsyncZeroClient,
        "call",
        new_callable=AsyncMock,
    ) as mock_call:
        mock_call.return_value = expected_response

        with pytest.raises(Exception) as exc_info:
            await image_to_animation.render_start_async(mvc_cfg_path)

        assert "failure occurred" in str(exc_info.value)


@pytest.mark.asyncio
async def test_image_to_animation_async_success():
    """
    Test that when the response contains 'status' equal to 'success',
    the function completes normally without raising an Exception.
    """
    mvc_cfg_path = Path("/test/path/config.json")
    expected_response = {"status": "success"}

    with patch.object(
        image_to_animation.AsyncZeroClient,
        "call",
        new_callable=AsyncMock,
    ) as mock_call:
        mock_call.return_value = expected_response

        result = await image_to_animation.render_start_async(mvc_cfg_path)
        # 성공 시 함수는 아무 값도 반환하지 않음 (None)
        assert result is None
