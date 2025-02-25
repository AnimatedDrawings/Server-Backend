from pathlib import Path
from typing import Optional


FILES_PATH = Path(__file__).parent.parent.joinpath("files")
ORIGIN_IMAGE_NAME = "origin_image.png"
BOUNDING_BOX_FILE_NAME = "bounding_box.yaml"
CROPPED_IMAGE_NAME = "cropped_image.png"
MASK_IMAGE_NAME = "mask_image.png"
CUTOUT_CHARACTER_IMAGE_NAME = "cutout_character_image.png"
CHAR_CFG_FILE_NAME = "char_cfg.yaml"


def get_base_path(
    ad_id: str,
    files_path: Optional[Path] = None,
) -> Path:
    files_path = files_path or FILES_PATH
    return files_path.joinpath(ad_id)
