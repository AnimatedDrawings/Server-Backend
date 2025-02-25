import cv2
from typing import Tuple
from cv2.typing import MatLike
from pathlib import Path
from fastapi import UploadFile
from ad_fast_api.domain.cutout_character.sources.errors import (
    cutout_character_400_status as cc4s,
    cutout_character_500_status as cc5s,
)
from ad_fast_api.workspace.sources import conf_workspace as cw
from logging import Logger
from ad_fast_api.snippets.sources.save_image import get_file_bytes, save_image_async


async def save_cutout_character_image_async(
    file: UploadFile,
    base_path: Path,
):
    file_bytes = get_file_bytes(file=file)
    if not file_bytes:
        raise cc4s.CUTOUT_CHARACTER_FILE_EMPTY_OR_INVALID

    await save_image_async(
        image_bytes=file_bytes,
        image_name=cw.CUTOUT_CHARACTER_IMAGE_NAME,
        base_path=base_path,
    )


def resize_cutout_image(
    base_path: Path,
    logger: Logger,
) -> Tuple[MatLike, MatLike]:
    # 경로 처리
    cropped_image_path = base_path / cw.CROPPED_IMAGE_NAME
    cutout_image_path = base_path / cw.CUTOUT_CHARACTER_IMAGE_NAME

    # cropped_image 읽기 (사이즈 기준)
    cropped_image = cv2.imread(str(cropped_image_path), cv2.IMREAD_UNCHANGED)
    if cropped_image is None:
        msg = cc5s.NOT_FOUND_CROPPED_IMAGE.format(cropped_image_path=cropped_image_path)
        logger.critical(msg)
        raise Exception(msg)
    height, width = cropped_image.shape[:2]

    # cutout_image 읽기
    cutout_image = cv2.imread(str(cutout_image_path), cv2.IMREAD_UNCHANGED)
    if cutout_image is None:
        msg = cc5s.NOT_FOUND_CUTOUT_CHARACTER_IMAGE.format(
            cutout_character_image_path=cutout_image_path
        )
        logger.critical(msg)
        raise Exception(msg)

    # 이미 크기가 동일하면 resize 생략
    if cutout_image.shape[0] == height and cutout_image.shape[1] == width:
        return (cropped_image, cutout_image)

    # 축소할 경우 INTER_AREA, 확대할 경우 INTER_LINEAR 사용
    if cutout_image.shape[0] > height or cutout_image.shape[1] > width:
        interp = cv2.INTER_AREA
    else:
        interp = cv2.INTER_LINEAR

    resized_cutout_image = cv2.resize(
        cutout_image, dsize=(width, height), interpolation=interp
    )

    if not cv2.imwrite(str(cutout_image_path), resized_cutout_image):
        msg = cc5s.FAILED_TO_WRITE_CUTOUT_IMAGE.format(
            cutout_image_path=cutout_image_path
        )
        logger.critical(msg)
        raise Exception(msg)

    return (cropped_image, resized_cutout_image)


def recreate_mask_image(
    cutout_image: MatLike,
    base_path: Path,
    logger: Logger,
):
    # 알파 채널 존재 여부 확인 (알파 채널은 4번째 채널에 위치)
    if cutout_image.shape[2] < 4:
        msg = cc5s.CUTOUT_CHARACTER_IMAGE_DOES_NOT_HAVE_ALPHA_CHANNEL
        logger.critical(msg)
        raise Exception(msg)

    # 알파 채널을 마스크 이미지로 추출
    mask_image = cutout_image[:, :, 3]

    # 마스크 이미지 저장 및 저장 성공 여부 확인
    mask_image_path = base_path / cw.MASK_IMAGE_NAME
    if not cv2.imwrite(str(mask_image_path), mask_image):
        msg = cc5s.FAILED_TO_WRITE_MASK_IMAGE.format(mask_image_path=mask_image_path)
        logger.critical(msg)
        raise Exception(msg)
