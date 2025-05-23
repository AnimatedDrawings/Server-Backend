from pathlib import Path
from typing import Optional

FILES_DIR_NAME = "files"
CONFIG_DIR_NAME = "config"

FILES_PATH = Path(__file__).parent.parent.joinpath(FILES_DIR_NAME)
ORIGIN_IMAGE_NAME = "origin_image.png"
BOUNDING_BOX_FILE_NAME = "bounding_box.yaml"
CROPPED_IMAGE_NAME = "texture.png"
MASK_IMAGE_NAME = "mask.png"
CUTOUT_CHARACTER_IMAGE_NAME = "cutout_character_image.png"
CHAR_CFG_FILE_NAME = "char_cfg.yaml"
VIDEO_DIR_NAME = "video"
MVC_CFG_FILE_NAME = "mvc_cfg.yaml"


def get_video_dir_path(
    base_path: Path,
) -> Path:
    return base_path.joinpath(VIDEO_DIR_NAME)


def get_video_file_name(ad_animation: str) -> str:
    return f"{ad_animation}.gif"


def get_base_path(
    ad_id: str,
    files_path: Optional[Path] = None,
) -> Path:
    files_path = files_path or FILES_PATH
    return files_path.joinpath(ad_id)
