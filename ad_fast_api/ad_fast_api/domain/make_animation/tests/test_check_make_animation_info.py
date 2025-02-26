import pytest
from fastapi import HTTPException
from ad_fast_api.domain.make_animation.sources.features import (
    check_make_animation_info as cmai,
)
from ad_fast_api.domain.make_animation.sources.make_animation_schema import (
    ADAnimation,
)
from ad_fast_api.workspace.sources.conf_workspace import (
    get_video_file_name,
    VIDEO_DIR_NAME,
)
from unittest.mock import patch


def test_valid_animations():
    """
    올바른 애니메이션 값을 인자로 주었을 때 예외가 발생하지 않는지 확인합니다.
    """
    # ADAnimation의 값들을 순회하면서 테스트합니다.
    # ADAnimation이 Enum이라면, value나 name속성을 확인할 수 있습니다.
    # 여기서는 간단하게 Enum 멤버 자체로 체크합니다.
    for valid_animation in ADAnimation:
        # 예외가 발생하지 않아야 하므로 단순히 호출만 합니다.
        cmai.check_available_animation(valid_animation)


def test_invalid_animation():
    """
    잘못된 애니메이션 값을 인자로 주었을 때 HTTPException(status_code=400)를 발생하는지 확인합니다.
    """
    invalid_value = "invalid_animation_value"
    with pytest.raises(HTTPException) as excinfo:
        cmai.check_available_animation(invalid_value)
    assert excinfo.value.status_code == 400
    assert "Invalid animation" in excinfo.value.detail


def test_is_video_file_exists_True(tmp_path):
    # given
    base_path = tmp_path
    video_dir_path = base_path / VIDEO_DIR_NAME
    video_dir_path.mkdir(exist_ok=True)

    ad_animation = ADAnimation.dab
    video_file_name = get_video_file_name(ad_animation)
    video_file_path = video_dir_path / video_file_name
    video_file_path.touch()

    # when
    with patch.object(
        cmai,
        "get_video_dir_path",
        return_value=video_dir_path,
    ):
        result = cmai.is_video_file_exists(
            base_path=base_path,
            ad_animation=ad_animation,
        )

    # then
    assert base_path.joinpath(VIDEO_DIR_NAME).exists()
    assert result is None


def test_is_video_file_exists_False(tmp_path):
    # given
    base_path = tmp_path
    video_dir_path = base_path / VIDEO_DIR_NAME
    ad_animation = ADAnimation.dab
    video_file_path = video_dir_path / get_video_file_name(ad_animation)

    # when
    with patch.object(
        cmai,
        "get_video_dir_path",
        return_value=video_dir_path,
    ):
        result = cmai.is_video_file_exists(
            base_path=base_path,
            ad_animation=ad_animation,
        )

    # then
    assert base_path.joinpath(VIDEO_DIR_NAME).exists()
    assert result == video_file_path
