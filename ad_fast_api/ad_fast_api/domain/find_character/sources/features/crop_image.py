import cv2
from pathlib import Path
from ad_fast_api.domain.schema.sources.schemas import BoundingBox
from ad_fast_api.workspace.sources import conf_workspace as cw
import numpy as np


def crop_image(
    base_path: Path,
    bounding_box: BoundingBox,
) -> np.ndarray:
    origin_image_path = base_path.joinpath(cw.ORIGIN_IMAGE_NAME)
    img = cv2.imread(origin_image_path.as_posix())

    cropped_image = img[
        bounding_box.top : bounding_box.bottom,
        bounding_box.left : bounding_box.right,
    ]

    return cropped_image
