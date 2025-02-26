from ad_fast_api.workspace.sources.conf_workspace import (
    CHAR_CFG_FILE_NAME,
    MVC_CFG_FILE_NAME,
)
from pathlib import Path
from ad_fast_api.snippets.sources.save_dict import dict_to_file
from ad_fast_api.configuration.sources.config_dir import CONFIG_DIR_PATH


def create_animated_drawing_dict(
    base_path: Path,
    ad_animation: str,
) -> dict:
    """
    Given a path to a directory with character annotations, a motion configuration file, and a retarget configuration file,
    creates an animation and saves it to {annotation_dir}/video.png
    """

    # package character_cfg_fn, motion_cfg_fn, and retarget_cfg_fn
    char_cfg_path = base_path.joinpath(CHAR_CFG_FILE_NAME)
    motion_cfg_path = CONFIG_DIR_PATH.joinpath(f"motion/{ad_animation}.yaml")
    retarget_cfg_path = CONFIG_DIR_PATH.joinpath("retarget/fair1_ppf.yaml")
    animated_drawing_dict = {
        "character_cfg": char_cfg_path.as_posix(),
        "motion_cfg": motion_cfg_path.as_posix(),
        "retarget_cfg": retarget_cfg_path.as_posix(),
    }

    return animated_drawing_dict


def create_mvc_config(
    animated_drawing_dict: dict,
    video_file_path: Path,
) -> dict:
    mvc_cfg = {
        "scene": {
            "ANIMATED_CHARACTERS": [animated_drawing_dict]
        },  # add the character to the scene
        "controller": {
            "MODE": "video_render",  # 'video_render' or 'interactive'
            "OUTPUT_VIDEO_PATH": video_file_path.as_posix(),  # set the output location
        },
    }

    return mvc_cfg


def save_mvc_config(
    mvc_cfg: dict,
    base_path: Path,
) -> Path:
    mvc_cfg_path = base_path.joinpath(MVC_CFG_FILE_NAME)
    dict_to_file(
        to_save_dict=mvc_cfg,
        file_path=mvc_cfg_path,
    )

    return mvc_cfg_path
