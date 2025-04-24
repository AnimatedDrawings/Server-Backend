import cv2
from pathlib import Path
from ad_fast_api.domain.upload_drawing.sources.errors import (
    upload_drawing_500_status as ud5s,
)
from typing import Optional
from logging import Logger
import numpy as np
import httpx
from numpy.typing import NDArray
import json
from ad_fast_api.domain.schema.sources.schemas import BoundingBox
from ad_fast_api.workspace.sources import conf_workspace as cw
from fastapi import HTTPException


DETECT_CHARACTER_TORCHSERVE_URL = (
    "http://ad_torchserve:8080/predictions/drawn_humanoid_detector"
)


def check_image_is_rgb(
    base_path: Path,
    logger: Logger,
    origin_image_name: Optional[str] = None,
) -> NDArray:
    origin_image_path = base_path.joinpath(origin_image_name or cw.ORIGIN_IMAGE_NAME)

    img = cv2.imread(origin_image_path.as_posix())

    # ensure it's rgb
    if len(img.shape) != 3:
        msg = ud5s.IMAGE_SHAPE_ERROR.format(
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


async def detect_character_from_origin_async(
    img: NDArray,
    logger: Logger,
    url: Optional[str] = None,
) -> httpx.Response:
    # convert to bytes and send to torchserve
    img_b = cv2.imencode(".png", img)[1].tobytes()
    request_data = {"data": img_b}

    timeout = httpx.Timeout(25)
    async with httpx.AsyncClient(verify=False, timeout=timeout) as client:
        try:
            resp = await client.post(
                url or DETECT_CHARACTER_TORCHSERVE_URL,
                files=request_data,
            )
        except Exception as e:
            msg = ud5s.DETECT_CHARACTER_TORCHSERVE_ERROR.format(resp=str(e))
            logger.critical(msg)
            raise Exception(msg)

        if resp.status_code == 503:
            msg = ud5s.DETECT_CHARACTER_TORCHSERVE_ERROR.format(resp=resp)
            logger.critical(
                f"{msg}, work load is too high, status code: {resp.status_code}"
            )
            raise HTTPException(
                status_code=503,
                detail=msg,
            )

        if resp.status_code >= 300:
            msg = ud5s.DETECT_CHARACTER_TORCHSERVE_ERROR.format(resp=resp)
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
        msg = ud5s.DETECTION_ERROR.format(
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
        msg = ud5s.NO_DETECTION_ERROR
        logger.critical(msg)
        raise Exception(msg)

    # otherwise, report # detected and score of highest.
    msg = ud5s.REPORT_HIGHEST_SCORE_DETECTION.format(
        count=len(detection_results),
        score=detection_results[0]["score"],
    )
    logger.info(msg)


def calculate_bounding_box(
    detection_results,
    logger: Logger,
) -> BoundingBox:
    # calculate the coordinates of the character bounding box
    try:
        bbox = np.array(detection_results[0]["bbox"])
        l, t, r, b = [round(x) for x in bbox]
        bounding_box = BoundingBox(left=l, top=t, right=r, bottom=b)
    except Exception as e:
        msg = ud5s.CALCULATE_BOUNDING_BOX_ERROR.format(
            error=e,
        )
        logger.critical(msg)
        raise Exception(msg)

    return bounding_box
