import pytest
from unittest.mock import patch
from ad_fast_api.domain.make_animation.sources.features import (
    check_make_animation_info as cmai,
)
from ad_fast_api.domain.make_animation.sources.make_animation_schema import ADAnimation
from ad_fast_api.workspace.sources.conf_workspace import (
    get_video_file_name,
    VIDEO_DIR_NAME,
)
from ad_fast_api.snippets.testings.mock_logger import mock_logger


def test_check_available_animation_success(mock_logger):
    """
    올바른 애니메이션 값을 인자로 주었을 때 예외가 발생하지 않는지 확인합니다.
    """
    for valid_animation in ADAnimation:
        cmai.check_available_animation(valid_animation, mock_logger)


def test_check_available_animation_raises_exception(mock_logger):
    """
    잘못된 애니메이션 값을 인자로 주었을 때 예외가 발생하는지 확인합니다.
    """

    # given
    invalid_value = "invalid_animation_value"

    # when
    with pytest.raises(Exception) as excinfo:
        cmai.check_available_animation(invalid_value, mock_logger)

    # then
    assert "Invalid animation" in str(excinfo.value)


def test_get_video_file_path(tmp_path, mock_logger):
    """
    파일이 존재하는 경우, get_video_file_path (True, relative_path)를 반환하는지 검증합니다.
    """
    base_path = tmp_path
    video_dir_path = base_path / VIDEO_DIR_NAME
    video_dir_path.mkdir(exist_ok=True)
    ad_animation = ADAnimation.dab.value
    video_file_name = get_video_file_name(ad_animation)
    video_file_path = video_dir_path / video_file_name
    video_file_path.touch()  # 파일 생성
    relative_video_file_path = video_file_path.relative_to(base_path)

    with patch.object(cmai, "get_video_dir_path", return_value=video_dir_path):
        expected_video_file_path, expected_relative_video_file_path = (
            cmai.get_video_file_path(
                base_path=base_path,
                ad_animation=ad_animation,
                logger=mock_logger,
            )
        )

    mock_logger.info.assert_called_once_with(
        f"Animation file exists: {video_file_path}"
    )
    assert video_file_path == expected_video_file_path
    assert relative_video_file_path == expected_relative_video_file_path
