import cv2
from pathlib import Path
from ad_fast_api.domain.schema.sources.schemas import BoundingBox
from ad_fast_api.workspace.sources import conf_workspace as cw
import numpy as np
from skimage import measure
from logging import Logger
from scipy import ndimage
from ad_fast_api.domain.find_character.sources.helpers import (
    find_character_string as fcs,
)


def crop_image(
    base_path: Path,
    bounding_box: BoundingBox,
):
    origin_image_path = base_path.joinpath(cw.ORIGIN_IMAGE_NAME)
    img = cv2.imread(str(origin_image_path))

    cropped = img[
        bounding_box.top : bounding_box.bottom,
        bounding_box.left : bounding_box.right,
    ]

    cropped_image_path = base_path.joinpath(cw.CROPPED_IMAGE_NAME)
    cv2.imwrite(str(cropped_image_path), cropped)


# async def save_contour

# save mask
# mask_image_path = base_path.joinpath("mask.png")
# try:
#     mask = segment(cropped)
# except:
#     return fail("Found no contours within image")
# cv2.imwrite(mask_image_path.as_posix(), mask)

# # create masked_image(texture + mask)
# masked_img = cropped.copy()
# masked_img = cv2.cvtColor(masked_img, cv2.COLOR_BGR2BGRA)
# masked_img[:, :, 3] = mask
# masked_image_path = base_path.joinpath("masked_img.png")
# cv2.imwrite(masked_image_path.as_posix(), masked_img)


# async def segment_character(
#     img: np.ndarray,
#     logger: Logger,
# ):
#     loop = asyncio.get_event_loop()

#     # 비동기적으로 이미지 처리 함수를 실행
#     img = await loop.run_in_executor(None, np.min, img, 2)

#     adaptive_threshold = await loop.run_in_executor(
#         None,
#         cv2.adaptiveThreshold,
#         img,
#         255,
#         cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
#         cv2.THRESH_BINARY,
#         115,
#         8,
#     )
#     img = await loop.run_in_executor(None, cv2.bitwise_not, adaptive_threshold)

#     # Morphological operations 비동기 실행
#     kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
#     img = await loop.run_in_executor(
#         None, cv2.morphologyEx, img, cv2.MORPH_CLOSE, kernel, 2
#     )
#     img = await loop.run_in_executor(
#         None, cv2.morphologyEx, img, cv2.MORPH_DILATE, kernel, 2
#     )

#     # Floodfill 비동기 실행
#     mask = np.zeros([img.shape[0] + 2, img.shape[1] + 2], np.uint8)
#     mask[1:-1, 1:-1] = img.copy()

#     im_floodfill = np.full(img.shape, 255, np.uint8)
#     h, w = img.shape[:2]

#     async def floodfill_seeds():
#         for x in range(0, w - 1, 10):
#             await loop.run_in_executor(
#                 None, cv2.floodFill, im_floodfill, mask, (x, 0), 0
#             )
#             await loop.run_in_executor(
#                 None, cv2.floodFill, im_floodfill, mask, (x, h - 1), 0
#             )
#         for y in range(0, h - 1, 10):
#             await loop.run_in_executor(
#                 None, cv2.floodFill, im_floodfill, mask, (0, y), 0
#             )
#             await loop.run_in_executor(
#                 None, cv2.floodFill, im_floodfill, mask, (w - 1, y), 0
#             )

#     await floodfill_seeds()

#     # 가장 큰 컨투어 유지 비동기 실행
#     im_floodfill[0, :] = 0
#     im_floodfill[-1, :] = 0
#     im_floodfill[:, 0] = 0
#     im_floodfill[:, -1] = 0

#     mask2 = await loop.run_in_executor(None, cv2.bitwise_not, im_floodfill)
#     contours = await loop.run_in_executor(None, measure.find_contours, mask2, 0.0)

#     biggest = 0
#     mask = None

#     for c in contours:
#         x = np.zeros(mask2.T.shape, np.uint8)
#         cv2.fillPoly(x, [np.int32(c)], 1)
#         size = len(np.where(x == 1)[0])
#         if size > biggest:
#             mask = x
#             biggest = size

#     if mask is None:
#         msg = fcs.FOUND_NO_CONTOURS_WITHIN_IMAGE
#         logger.critical(msg)
#         raise Exception(msg)

#     mask = await loop.run_in_executor(None, ndimage.binary_fill_holes, mask)
#     mask = (255 * mask.astype(np.uint8)).T

#     return mask


# def segment_character(
#     img: np.ndarray,
#     logger: Logger,
# ):
#     """threshold"""
#     img = np.min(img, axis=2)
#     img = cv2.adaptiveThreshold(
#         img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 115, 8
#     )
#     img = cv2.bitwise_not(img)

#     """ morphops """
#     kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
#     img = cv2.morphologyEx(img, cv2.MORPH_CLOSE, kernel, iterations=2)
#     img = cv2.morphologyEx(img, cv2.MORPH_DILATE, kernel, iterations=2)

#     """ floodfill """
#     mask = np.zeros([img.shape[0] + 2, img.shape[1] + 2], np.uint8)
#     mask[1:-1, 1:-1] = img.copy()

#     # im_floodfill is results of floodfill. Starts off all white
#     im_floodfill = np.full(img.shape, 255, np.uint8)

#     # choose 10 points along each image side. use as seed for floodfill.
#     h, w = img.shape[:2]
#     for x in range(0, w - 1, 10):
#         cv2.floodFill(im_floodfill, mask, (x, 0), (0,))
#         cv2.floodFill(im_floodfill, mask, (x, h - 1), (0,))
#     for y in range(0, h - 1, 10):
#         cv2.floodFill(im_floodfill, mask, (0, y), (0,))
#         cv2.floodFill(im_floodfill, mask, (w - 1, y), (0,))

#     # make sure edges aren't character. necessary for contour finding
#     im_floodfill[0, :] = 0
#     im_floodfill[-1, :] = 0
#     im_floodfill[:, 0] = 0
#     im_floodfill[:, -1] = 0

#     """ retain largest contour """
#     mask2 = cv2.bitwise_not(im_floodfill)
#     mask = None
#     biggest = 0

#     contours = measure.find_contours(mask2, 0.0)
#     for c in contours:
#         x = np.zeros(mask2.T.shape, np.uint8)
#         cv2.fillPoly(x, [c.astype(np.int32)], (1,))
#         size = len(np.where(x == 1)[0])
#         if size > biggest:
#             mask = x
#             biggest = size

#     if mask is None:
#         msg = fcs.FOUND_NO_CONTOURS_WITHIN_IMAGE
#         logger.critical(msg)
#         raise Exception(msg)

#     mask_binary = ndimage.binary_fill_holes(mask)

#     if mask_binary is None:
#         msg = fcs.FOUND_NO_CONTOURS_WITHIN_IMAGE
#         logger.critical(msg)
#         raise Exception(msg)

#     mask = 255 * mask_binary.astype(np.uint8)

#     return mask.T


def segment_character(
    img: np.ndarray,
    logger: Logger,
):
    """Optimized character segmentation

    성능 개선을 위해 아래와 같이 최적화 하였습니다.
      - Floodfill 시드 포인트 생성을 리스트로 합침
      - cv2.findContours를 사용해 컨투어 검출 속도 개선
      - 불필요한 반복문 및 복사 최소화
    """
    # 그레이스케일 변환 (필요에 따라 cv2.cvtColor로 변경 가능)
    gray = np.min(img, axis=2)

    # Adaptive thresholding 적용
    thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 115, 8
    )
    thresh = cv2.bitwise_not(thresh)

    # 형태학적 연산: 닫기(Closing) -> 팽창(Dilation)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    morph = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)
    morph = cv2.morphologyEx(morph, cv2.MORPH_DILATE, kernel, iterations=2)

    # Floodfill 처리: 이미지 테두리에서 seed point들을 이용하여 내부 채우기
    h, w = morph.shape[:2]
    floodfill_mask = np.zeros((h + 2, w + 2), np.uint8)
    im_floodfill = np.full((h, w), 255, np.uint8)

    # 이미지 테두리의 seed point들을 한 번에 생성
    seed_points = (
        [(x, 0) for x in range(0, w, 10)]
        + [(x, h - 1) for x in range(0, w, 10)]
        + [(0, y) for y in range(0, h, 10)]
        + [(w - 1, y) for y in range(0, h, 10)]
    )
    for seed in seed_points:
        cv2.floodFill(im_floodfill, floodfill_mask, seed, (0,))

    # 테두리가 문자 영역으로 인식되지 않도록 강제로 0 처리
    im_floodfill[0, :] = 0
    im_floodfill[-1, :] = 0
    im_floodfill[:, 0] = 0
    im_floodfill[:, -1] = 0

    # 컨투어 검출을 위해 이미지 반전
    inv_img = cv2.bitwise_not(im_floodfill)

    # cv2.findContours를 사용하여 외부 컨투어만 추출 (속도 측면에서 우수)
    contours, _ = cv2.findContours(inv_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        msg = fcs.FOUND_NO_CONTOURS_WITHIN_IMAGE
        logger.critical(msg)
        raise Exception(msg)

    # 가장 큰 컨투어 선택
    largest_contour = max(contours, key=cv2.contourArea)

    # 가장 큰 컨투어로 마스크 생성
    largest_mask = np.zeros(inv_img.shape, np.uint8)
    cv2.drawContours(largest_mask, [largest_contour], -1, (1,), thickness=cv2.FILLED)

    # 구멍 채우기 (binary_fill_holes)
    filled_mask = ndimage.binary_fill_holes(largest_mask)
    if filled_mask is not None:
        filled_mask = filled_mask.astype(np.uint8)
        final_mask = 255 * filled_mask  # 0~255 범위의 binary mask
    else:
        final_mask = largest_mask * 255

    return final_mask.T
