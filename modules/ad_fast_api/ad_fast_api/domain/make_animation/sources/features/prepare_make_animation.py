from ad_fast_api.workspace.sources.conf_workspace import (
    CHAR_CFG_FILE_NAME,
    CONFIG_DIR_NAME,
)
from pathlib import Path
from ad_fast_api.snippets.sources.save_dict import dict_to_file
from typing import Protocol


class CameraConfig(Protocol):
    CAMERA_POS: list[float]
    CAMERA_FWD: list[float]


class DabCameraConfig(CameraConfig):
    CAMERA_POS: list[float] = [0.0, 0.9, 2.0]
    CAMERA_FWD: list[float] = [0.0, 0.5, 2.0]


class ZombieCameraConfig(CameraConfig):
    CAMERA_POS: list[float] = [1.0, 0.7, 4.0]
    CAMERA_FWD: list[float] = [0.0, 0.5, 4.0]


def get_camera_config(ad_animation: str) -> CameraConfig:
    if ad_animation == "dab":
        return DabCameraConfig()
    elif ad_animation == "zombie":
        return ZombieCameraConfig()
    else:
        raise ValueError(f"Invalid animation: {ad_animation}")


def create_mvc_config(
    animated_drawings_dict: dict,
    video_file_path: Path,
    ad_animation: str,
) -> dict:
    camera_config = get_camera_config(ad_animation)

    mvc_cfg_dict = {
        "scene": {
            "ANIMATED_CHARACTERS": [animated_drawings_dict]
        },  # add the character to the scene
        "view": {
            "USE_MESA": True,
            "CAMERA_POS": camera_config.CAMERA_POS,
            "CAMERA_FWD": camera_config.CAMERA_FWD,
        },
        "controller": {
            "MODE": "video_render",  # 'video_render' or 'interactive'
            "OUTPUT_VIDEO_PATH": video_file_path.as_posix(),  # set the output location
        },
    }

    return mvc_cfg_dict


def create_animated_drawing_dict(
    animated_drawings_base_path: Path,
    animated_drawings_workspace_path: Path,
    ad_animation: str,
) -> dict:
    """
    Given a path to a directory with character annotations, a motion configuration file, and a retarget configuration file,
    creates an animation and saves it to {annotation_dir}/video.png
    """

    # package character_cfg_fn, motion_cfg_fn, and retarget_cfg_fn
    char_cfg_path = animated_drawings_base_path.joinpath(CHAR_CFG_FILE_NAME)

    config_dir_path = animated_drawings_workspace_path.joinpath(CONFIG_DIR_NAME)
    motion_cfg_path = config_dir_path.joinpath(f"motion/{ad_animation}.yaml")
    retarget_cfg_path = config_dir_path.joinpath("retarget/fair1_ppf.yaml")

    animated_drawing_dict = {
        "character_cfg": char_cfg_path.as_posix(),
        "motion_cfg": motion_cfg_path.as_posix(),
        "retarget_cfg": retarget_cfg_path.as_posix(),
    }

    return animated_drawing_dict


def save_mvc_config(
    mvc_cfg_file_name: str,
    mvc_cfg_dict: dict,
    base_path: Path,
):
    mvc_cfg_path = base_path.joinpath(mvc_cfg_file_name)
    dict_to_file(
        to_save_dict=mvc_cfg_dict,
        file_path=mvc_cfg_path,
    )
