import cv2
import numpy as np
from cv2.typing import MatLike
import httpx
from typing import Optional
from ad_fast_api.domain.cutout_character.sources.errors import (
    cutout_character_500_status as cc5s,
)
from ad_fast_api.workspace.sources import conf_workspace as cw
from logging import Logger
import json
from pathlib import Path
from ad_fast_api.workspace.sources.conf_workspace import CHAR_CFG_FILE_NAME
from ad_fast_api.snippets.sources.save_dict import dict_to_file


GET_SKELETON_TORCHSERVE_URL = (
    "http://torchserve:8080/predictions/drawn_humanoid_pose_estimator"
)


def get_cropped_image(
    base_path: Path,
    logger: Logger,
):
    cropped_image_path = base_path / cw.CROPPED_IMAGE_NAME
    cropped_image = cv2.imread(cropped_image_path.as_posix())
    if cropped_image is None:
        msg = cc5s.NOT_FOUND_CROPPED_IMAGE.format(cropped_image_path=cropped_image_path)
        logger.critical(msg)
        raise Exception(msg)

    return cropped_image


async def get_pose_result_async(
    cropped_image,
    logger: Logger,
    url: Optional[str] = None,
) -> list[dict] | dict:
    img_b = cv2.imencode(".png", cropped_image)[1].tobytes()
    request_data = {"data": img_b}

    timeout = httpx.Timeout(60)
    async with httpx.AsyncClient(verify=False, timeout=timeout) as client:
        try:
            resp = await client.post(
                url or GET_SKELETON_TORCHSERVE_URL,
                files=request_data,
            )
        except Exception as e:
            msg = cc5s.GET_SKELETON_TORCHSERVE_ERROR.format(resp=str(e))
            logger.critical(msg)
            raise Exception(msg)

        if resp is None or resp.status_code >= 300:
            msg = cc5s.GET_SKELETON_TORCHSERVE_ERROR.format(resp=resp)
            logger.critical(msg)
            raise Exception(msg)

        pose_results = json.loads(resp.content)
        return pose_results


def get_pose_result(
    cropped_image: MatLike,
    logger: Logger,
    url: Optional[str] = None,
) -> list[dict] | dict:
    data_file = {"data": cv2.imencode(".png", cropped_image)[1].tobytes()}
    with httpx.Client(verify=False) as client:
        try:
            resp = client.post(
                url or GET_SKELETON_TORCHSERVE_URL,
                files=data_file,
            )
        except Exception as e:
            msg = cc5s.GET_SKELETON_TORCHSERVE_ERROR.format(resp=str(e))
            logger.critical(msg)
            raise Exception(msg)

        if resp is None or resp.status_code >= 300:
            msg = cc5s.GET_SKELETON_TORCHSERVE_ERROR.format(resp=resp)
            logger.critical(msg)
            raise Exception(msg)

        pose_results = json.loads(resp.content)
        return pose_results


def check_pose_results(
    pose_results: list[dict] | dict,
    logger: Logger,
) -> np.ndarray:
    if (
        type(pose_results) == dict
        and "code" in pose_results.keys()
        and pose_results["code"] == 404
    ):
        msg = cc5s.POSE_ESTIMATION_ERROR.format(pose_results=pose_results)
        logger.critical(msg)
        raise Exception(msg)

    # if cannot detect any skeleton, abort
    if len(pose_results) == 0:
        msg = cc5s.NO_SKELETON_DETECTED
        logger.critical(msg)
        raise Exception(msg)

    # if more than one skeleton detected, abort
    if 1 < len(pose_results):
        msg = cc5s.MORE_THAN_ONE_SKELETON_DETECTED.format(
            len_pose_results=len(pose_results)
        )
        logger.critical(msg)
        raise Exception(msg)

    # get x y coordinates of detection joint keypoints
    kpts = np.array(pose_results[0]["keypoints"])[:, :2]
    return kpts


def make_skeleton(
    kpts: np.ndarray,
) -> list:
    # use them to build character skeleton rig
    skeleton = []
    skeleton.append(
        {
            "loc": [round(x) for x in (kpts[11] + kpts[12]) / 2],
            "name": "root",
            "parent": None,
        }
    )
    skeleton.append(
        {
            "loc": [round(x) for x in (kpts[11] + kpts[12]) / 2],
            "name": "hip",
            "parent": "root",
        }
    )
    skeleton.append(
        {
            "loc": [round(x) for x in (kpts[5] + kpts[6]) / 2],
            "name": "torso",
            "parent": "hip",
        }
    )
    skeleton.append(
        {"loc": [round(x) for x in kpts[0]], "name": "neck", "parent": "torso"}
    )
    skeleton.append(
        {
            "loc": [round(x) for x in kpts[6]],
            "name": "right_shoulder",
            "parent": "torso",
        }
    )
    skeleton.append(
        {
            "loc": [round(x) for x in kpts[8]],
            "name": "right_elbow",
            "parent": "right_shoulder",
        }
    )
    skeleton.append(
        {
            "loc": [round(x) for x in kpts[10]],
            "name": "right_hand",
            "parent": "right_elbow",
        }
    )
    skeleton.append(
        {"loc": [round(x) for x in kpts[5]], "name": "left_shoulder", "parent": "torso"}
    )
    skeleton.append(
        {
            "loc": [round(x) for x in kpts[7]],
            "name": "left_elbow",
            "parent": "left_shoulder",
        }
    )
    skeleton.append(
        {
            "loc": [round(x) for x in kpts[9]],
            "name": "left_hand",
            "parent": "left_elbow",
        }
    )
    skeleton.append(
        {"loc": [round(x) for x in kpts[12]], "name": "right_hip", "parent": "root"}
    )
    skeleton.append(
        {
            "loc": [round(x) for x in kpts[14]],
            "name": "right_knee",
            "parent": "right_hip",
        }
    )
    skeleton.append(
        {
            "loc": [round(x) for x in kpts[16]],
            "name": "right_foot",
            "parent": "right_knee",
        }
    )
    skeleton.append(
        {"loc": [round(x) for x in kpts[11]], "name": "left_hip", "parent": "root"}
    )
    skeleton.append(
        {"loc": [round(x) for x in kpts[13]], "name": "left_knee", "parent": "left_hip"}
    )
    skeleton.append(
        {
            "loc": [round(x) for x in kpts[15]],
            "name": "left_foot",
            "parent": "left_knee",
        }
    )

    return skeleton


def save_char_cfg(
    skeleton: list,
    cropped_image: MatLike,
    base_path: Path,
) -> dict:
    # create the character config dictionary
    char_cfg = {
        "skeleton": skeleton,
        "height": cropped_image.shape[0],
        "width": cropped_image.shape[1],
    }
    char_cfg_path = base_path.joinpath(CHAR_CFG_FILE_NAME)
    dict_to_file(
        to_save_dict=char_cfg,
        file_path=char_cfg_path,
    )

    return char_cfg
