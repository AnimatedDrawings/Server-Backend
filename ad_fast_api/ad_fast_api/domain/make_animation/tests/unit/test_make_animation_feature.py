from fastapi import HTTPException
import pytest
from pathlib import Path
from unittest.mock import patch, AsyncMock
from ad_fast_api.domain.make_animation.sources.features import make_animation_feature
from ad_fast_api.workspace.sources.conf_workspace import FILES_DIR_NAME
from ad_fast_api.snippets.sources.ad_env import ADEnv


@patch.object(make_animation_feature, "check_available_animation")
@patch.object(make_animation_feature, "is_video_file_exists")
def test_check_make_animation_info_success(
    mock_is_video_file_exists, mock_check_available_animation
):
    # 준비
    base_path = Path("/test/path")
    ad_animation = "walk"
    expected_path = Path("/test/path/video.mp4")
    mock_is_video_file_exists.return_value = expected_path

    # 실행
    result = make_animation_feature.check_make_animation_info(base_path, ad_animation)

    # 검증
    mock_check_available_animation.assert_called_once_with(ad_animation=ad_animation)
    mock_is_video_file_exists.assert_called_once_with(
        base_path=base_path, ad_animation=ad_animation
    )
    assert result == expected_path


@patch.object(make_animation_feature, "check_available_animation")
@patch.object(make_animation_feature, "is_video_file_exists")
def test_check_make_animation_info_no_video(
    mock_is_video_file_exists, mock_check_available_animation
):
    # 준비
    base_path = Path("/test/path")
    ad_animation = "walk"
    mock_is_video_file_exists.return_value = None

    # 실행
    result = make_animation_feature.check_make_animation_info(base_path, ad_animation)

    # 검증
    mock_check_available_animation.assert_called_once_with(ad_animation=ad_animation)
    mock_is_video_file_exists.assert_called_once_with(
        base_path=base_path, ad_animation=ad_animation
    )
    assert result is None


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


import pytest
from pathlib import Path
from unittest.mock import patch, AsyncMock

# from ad_fast_api.ad_fast_api.domain.make_animation.sources.features import make_animation_feature


@pytest.mark.asyncio
async def test_image_to_animation_async_no_status():
    """
    Test that when the response is None or missing the 'status' key,
    the function raises an Exception with a message indicating failure.
    """
    mvc_cfg_path = Path("/test/path/config.json")
    # 응답이 None 인 경우: "status" 키조차 존재하지 않음.
    expected_response = None

    with patch.object(
        make_animation_feature.zero_client,
        "call",
        new_callable=AsyncMock,
    ) as mock_call:
        mock_call.return_value = expected_response

        with pytest.raises(Exception) as exc_info:
            await make_animation_feature.image_to_animation_async(mvc_cfg_path)

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
        make_animation_feature.zero_client,
        "call",
        new_callable=AsyncMock,
    ) as mock_call:
        mock_call.return_value = expected_response

        with pytest.raises(Exception) as exc_info:
            await make_animation_feature.image_to_animation_async(mvc_cfg_path)

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
        make_animation_feature.zero_client,
        "call",
        new_callable=AsyncMock,
    ) as mock_call:
        mock_call.return_value = expected_response

        result = await make_animation_feature.image_to_animation_async(mvc_cfg_path)
        # 성공 시 함수는 아무 값도 반환하지 않음 (None)
        assert result is None


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
