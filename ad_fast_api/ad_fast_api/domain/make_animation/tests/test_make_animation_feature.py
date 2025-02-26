from ad_fast_api.domain.make_animation.sources.features import (
    prepare_make_animation as pma,
)
from ad_fast_api.domain.make_animation.sources.make_animation_schema import (
    ADAnimation,
)
from ad_fast_api.workspace.sources.conf_workspace import (
    CHAR_CFG_FILE_NAME,
    MVC_CFG_FILE_NAME,
)
from unittest.mock import patch, MagicMock
from pathlib import Path


def test_create_animated_drawing_dict(tmp_path):
    # given
    base_path = tmp_path
    ad_animation = ADAnimation.dab
    mock_config_dir_path = Path("/mock/config/dir")

    # when
    with patch.object(
        pma,
        "CONFIG_DIR_PATH",
        mock_config_dir_path,
    ):
        result = pma.create_animated_drawing_dict(
            base_path=base_path,
            ad_animation=ad_animation,
        )

    # then
    assert result["character_cfg"] == base_path.joinpath(CHAR_CFG_FILE_NAME).as_posix()
    assert (
        result["motion_cfg"]
        == mock_config_dir_path.joinpath(f"motion/{ad_animation}.yaml").as_posix()
    )
    assert (
        result["retarget_cfg"]
        == mock_config_dir_path.joinpath("retarget/fair1_ppf.yaml").as_posix()
    )


def test_create_mvc_config():
    # given
    animated_drawing_dict = {
        "character_cfg": "/path/to/character.yaml",
        "motion_cfg": "/path/to/motion.yaml",
        "retarget_cfg": "/path/to/retarget.yaml",
    }
    video_file_path = Path("/path/to/output/video.mp4")

    # when
    result = pma.create_mvc_config(
        animated_drawing_dict=animated_drawing_dict,
        video_file_path=video_file_path,
    )

    # then
    assert result["scene"]["ANIMATED_CHARACTERS"] == [animated_drawing_dict]
    assert result["controller"]["MODE"] == "video_render"
    assert result["controller"]["OUTPUT_VIDEO_PATH"] == video_file_path.as_posix()


def test_save_mvc_config(tmp_path):
    # given
    base_path = tmp_path
    mvc_cfg = {
        "scene": {"ANIMATED_CHARACTERS": [{}]},
        "controller": {
            "MODE": "video_render",
            "OUTPUT_VIDEO_PATH": "/path/to/video.mp4",
        },
    }
    expected_mvc_cfg_path = base_path.joinpath(MVC_CFG_FILE_NAME)

    # when
    with patch.object(
        pma,
        "dict_to_file",
        MagicMock(),
    ) as mock_dict_to_file:
        result = pma.save_mvc_config(
            mvc_cfg=mvc_cfg,
            base_path=base_path,
        )

    # then
    assert result == expected_mvc_cfg_path
    mock_dict_to_file.assert_called_once_with(
        to_save_dict=mvc_cfg,
        file_path=expected_mvc_cfg_path,
    )
