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
import json
import yaml
import aiofiles


TORCHSERVE_URL = "http://torchserve:8080/predictions/drawn_humanoid_detector"
BOUNDING_BOX_FILE_NAME = "bounding_box.yaml"


IMAGE_SHAPE_ERROR = "image must have 3 channels (rgb). Found {len_shape}"
SEND_TO_TORCHSERVE_ERROR = "Failed to get bounding box, please check if the 'docker_torchserve' is running and healthy, resp: {resp}"
DETECTION_ERROR = "Error performing detection. Check that drawn_humanoid_detector.mar was properly downloaded. Response: {detection_results}"
NO_DETECTION_ERROR = "Could not detect any drawn humanoids in the image. Aborting"
REPORT_HIGHEST_SCORE_DETECTION = (
    "Detected {count} humanoids in image. Using detection with highest score {score}."
)
CALCULATE_BOUNDING_BOX_ERROR = "Error calculating bounding box. Error: {error}"


def check_image_is_rgb(
    base_path: Path,
    logger: Logger,
    origin_image_name: Optional[str] = None,
) -> NDArray:
    origin_image_path = base_path.joinpath(origin_image_name or ORIGIN_IMAGE_NAME)

    img = cv2.imread(origin_image_path.as_posix())

    # ensure it's rgb
    if len(img.shape) != 3:
        msg = IMAGE_SHAPE_ERROR.format(
            len_shape=len(
                img.shape,
            )
        )
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


async def send_to_torchserve(
    img: NDArray,
    logger: Logger,
    url: Optional[str] = None,
) -> httpx.Response:
    # convert to bytes and send to torchserve
    img_b = cv2.imencode(".png", img)[1].tobytes()
    request_data = {"data": img_b}

    async with httpx.AsyncClient(verify=False) as client:
        try:
            resp = await client.post(
                url or TORCHSERVE_URL,
                files=request_data,
            )
        except Exception as e:
            msg = SEND_TO_TORCHSERVE_ERROR.format(resp=str(e))
            logger.critical(msg)
            raise Exception(msg)

        if resp.status_code >= 300:
            msg = SEND_TO_TORCHSERVE_ERROR.format(resp=resp)
            logger.critical(msg)
            raise Exception(msg)

        return resp


def check_detection_results(
    resp: httpx.Response,
    logger: Logger,
):
    detection_results = json.loads(resp.content)
    if (
        isinstance(detection_results, dict)
        and "code" in detection_results.keys()
        and detection_results["code"] == 404
    ):
        msg = DETECTION_ERROR.format(
            detection_results=detection_results,
        )
        logger.critical(msg)
        raise Exception(msg)

    return detection_results


def sort_detection_results(
    detection_results,
    logger: Logger,
):
    detection_results.sort(key=lambda x: x["score"], reverse=True)

    if len(detection_results) == 0:
        msg = NO_DETECTION_ERROR
        logger.critical(msg)
        raise Exception(msg)

    # otherwise, report # detected and score of highest.
    msg = REPORT_HIGHEST_SCORE_DETECTION.format(
        count=len(detection_results),
        score=detection_results[0]["score"],
    )
    logger.info(msg)


def calculate_bounding_box(
    detection_results,
    logger: Logger,
) -> dict:
    # calculate the coordinates of the character bounding box
    try:
        bbox = np.array(detection_results[0]["bbox"])
        l, t, r, b = [round(x) for x in bbox]
        bounding_box = {"left": l, "top": t, "right": r, "bottom": b}
    except Exception as e:
        msg = CALCULATE_BOUNDING_BOX_ERROR.format(
            error=e,
        )
        logger.critical(msg)
        raise Exception(msg)

    return bounding_box


async def save_bounding_box(
    bounding_box: dict,
    base_path: Path,
):
    # dump the bounding box results to file asynchronously
    bounding_box_path = base_path.joinpath(BOUNDING_BOX_FILE_NAME)
    content = yaml.dump(bounding_box)
    async with aiofiles.open(bounding_box_path.as_posix(), "w") as f:
        await f.write(content)


async def detect_character(ad_id: str):
    base_path = get_base_path(ad_id=ad_id)

    logger = setup_logger(
        base_path=base_path,
    )

    img = check_image_is_rgb(
        base_path=base_path,
        logger=logger,
    )
    img = resize_image(img=img)

    resp = await send_to_torchserve(
        img=img,
        logger=logger,
    )

    detection_results = check_detection_results(
        resp=resp,
        logger=logger,
    )
    sort_detection_results(
        detection_results=detection_results,
        logger=logger,
    )

    bounding_box = calculate_bounding_box(
        detection_results=detection_results,
        logger=logger,
    )
    await save_bounding_box(
        bounding_box=bounding_box,
        base_path=base_path,
    )
