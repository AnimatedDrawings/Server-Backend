import cv2
import numpy as np


def remove_background(
    cropped_image: np.ndarray,
    mask_image: np.ndarray,
) -> np.ndarray:
    # cropped_image를 BGRA로 변환합니다.
    removed_bg_image = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2BGRA)

    # mask_image가 3채널(BGR) 이미지면 그레이스케일로 변환하고,
    # 이미 단일 채널이면 복사하여 사용합니다.
    if mask_image.ndim == 3 and mask_image.shape[2] == 3:
        mask_gray = cv2.cvtColor(mask_image, cv2.COLOR_BGR2GRAY)
    else:
        mask_gray = mask_image.copy()

    # 알파 채널에 mask_gray를 할당합니다.
    removed_bg_image[:, :, 3] = mask_gray
    return removed_bg_image
