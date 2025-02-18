import cv2
from pathlib import Path
from ad_fast_api.domain.upload_drawing.sources.features.configure_work_dir import (
    ORIGIN_IMAGE_NAME,
)
from ad_fast_api.workspace.sources.work_dir import get_base_path
from typing import Optional
from logging import Logger
from ad_fast_api.snippets.sources.logger import setup_logger
import numpy as np
import httpx
from numpy.typing import NDArray


IMAGE_SHAPE_ERROR = "image must have 3 channels (rgb). Found"
TORCHSERVE_URL = "http://torchserve:8080/predictions/drawn_humanoid_detector"
SEND_TO_TORCHSERVE_ERROR = "Failed to get bounding box, please check if the 'docker_torchserve' is running and healthy, resp:"


def check_image_is_rgb(
    base_path: Path,
    logger: Logger,
    origin_image_name: Optional[str] = None,
) -> NDArray:
    origin_image_path = base_path.joinpath(origin_image_name or ORIGIN_IMAGE_NAME)

    img = cv2.imread(origin_image_path.as_posix())

    # ensure it's rgb
    if len(img.shape) != 3:
        msg = f"{IMAGE_SHAPE_ERROR} {len(img.shape)}"
        logger.critical(msg)
        raise Exception(msg)

    return img


def resize_image(img: NDArray) -> NDArray:
    # resize if needed
    if np.max(img.shape) > 1000:
        scale = 1000 / np.max(img.shape)
        img = cv2.resize(
            img, (round(scale * img.shape[1]), round(scale * img.shape[0]))
        )

    return img


def send_to_torchserve(
    img: NDArray,
    logger: Logger,
    url: Optional[str] = None,
):
    # convert to bytes and send to torchserve
    img_b = cv2.imencode(".png", img)[1].tobytes()
    request_data = {"data": img_b}
    resp = httpx.post(
        url or TORCHSERVE_URL,
        files=request_data,
        verify=False,
    )
    if resp is None or resp.status_code >= 300:
        msg = f"{SEND_TO_TORCHSERVE_ERROR} {resp}"
        logger.critical(msg)
        raise Exception(msg)


def detect_character(ad_id: str):
    base_path = get_base_path(ad_id=ad_id)

    logger = setup_logger(
        base_path=base_path,
    )

    img = check_image_is_rgb(
        base_path=base_path,
        logger=logger,
    )
    img = resize_image(img=img)

    send_to_torchserve(
        img=img,
        logger=logger,
    )
