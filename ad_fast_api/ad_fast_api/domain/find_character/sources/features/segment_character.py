import cv2
import numpy as np
from skimage import measure
from logging import Logger
from scipy import ndimage
from ad_fast_api.domain.find_character.sources.helpers import (
    find_character_string as fcs,
)


def apply_threshold(img: np.ndarray) -> np.ndarray:
    """
    이미지의 각 픽셀에 대해 RGB 채널의 최솟값을 취해 그레이스케일 이미지로 변환한 후,
    적응형 임계값(adaptive threshold)을 적용하여 이진 이미지를 생성하고,
    최종적으로 색상을 반전(bitwise not)시킵니다.
    """
    # 그레이스케일 변환: 각 픽셀에서 3개 채널 중 최소값 선택
    gray = np.min(img, axis=2)

    # 적응형 임계값: Gaussian 방식 적용, 블록 크기 115, 상수 8
    binary = cv2.adaptiveThreshold(
        src=gray,  # 입력 이미지 (그레이스케일, 단일 채널)
        maxValue=255,  # 임계값을 넘었을 때 적용할 값, 흰색
        adaptiveMethod=cv2.ADAPTIVE_THRESH_GAUSSIAN_C,  # 적응형 방법
        thresholdType=cv2.THRESH_BINARY,  # 이진화 타입
        blockSize=115,  # 주변 영역 크기
        C=8,  # 계산된 평균이나 가중평균에서 차감할 상수
    )

    """
    - cv2.ADAPTIVE_THRESH_GAUSSIAN_C
    가우시안 가중치 예시, 중심에 가까운 픽셀에 더 높은 가중치 부여
    [0.1 0.2 0.1]
    [0.2 0.8 0.2]
    [0.1 0.2 0.1]

    - cv2.THRESH_BINARY
    if pixel > threshold:
        pixel = maxValue  # 255
     else:
        pixel = 0
    """

    # 색상 반전: 배경과 전경을 뒤집음
    return cv2.bitwise_not(binary)


def apply_morphology(binary_img: np.ndarray) -> np.ndarray:
    """
    형태학적 변환으로 노이즈를 제거하고 객체 윤곽을 강화합니다.
    - MORPH_CLOSE: 작은 홀(구멍)들을 메움.
    - MORPH_DILATE: 객체의 경계를 확장하여 강조함.

    원본 이진화 이미지
        ↓
    클로징 (2회) - 작은 구멍과 끊어진 부분 보완
        ↓
    팽창 (2회) - 객체를 굵게 만들고 경계 강화
    """

    # 3×3 크기의 사각형 구조 요소(커널)를 생성
    # cv2.MORPH_RECT: 사각형 모양의 커널을 생성
    # (3, 3): 커널의 크기를 지정
    # 이 커널은 이후 연산의 기본 단위로 사용됨
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))

    # 클로징은 팽창(Dilation) 후 침식(Erosion)을 순차적으로 적용하는 연산입니다:
    """
    1. 팽창 과정:
    - 커널이 걸쳐진 영역에 1이 하나라도 있으면 중심을 1로 설정
    - 객체가 확장되고 작은 구멍이 채워짐

    2. 침식 과정:
    - 커널이 걸쳐진 영역에 1이 모두 있어야 중심을 1로 설정
    - 객체의 전체적인 크기는 유지하면서 경계가 부드러워짐
    - 작은 구멍이나 끊어진 부분이 메워짐
    """
    closed = cv2.morphologyEx(binary_img, cv2.MORPH_CLOSE, kernel, iterations=2)

    # 팽창 연산: 객체 경계를 확장 (반복 2회)
    dilated = cv2.morphologyEx(closed, cv2.MORPH_DILATE, kernel, iterations=2)

    return dilated


def apply_floodfill(processed_img: np.ndarray) -> np.ndarray:
    """
    플러드 필(Flood Fill) 기법은 이미지 내에서 연결된 영역(Region) 을 효율적으로 찾아내어 일정 조건(예: 색상, 밝기 등)에 해당하는 픽셀들을 한꺼번에 채우는 알고리즘입니다.
    보통 그래픽 편집 도구에서 “버킷 채우기(Bucket Fill)”로 알려져 있으며, 영역 분할이나 배경 제거 같은 작업에 유용하게 사용됩니다.
    이미지 가장자리에서 여러 포인트로부터 플러드 필을 수행하여 배경을 제거합니다.
    가장자리에 있는 영역은 배경(0)으로 채워지며, 이후 해당 결과를 이용해 올바른 객체 영역을 추출합니다.
    """
    h, w = processed_img.shape[:2]

    # OpenCV의 floodFill은 원본보다 2픽셀 큰 마스크를 요구함
    flood_mask = np.zeros([h + 2, w + 2], np.uint8)
    flood_mask[1:-1, 1:-1] = processed_img.copy()

    # floodfill 결과를 담을 이미지. 처음에는 모두 흰색(255)로 초기화
    im_floodfill = np.full(processed_img.shape, 255, np.uint8)

    # 10픽셀 간격으로 이미지의 상하단 가장자리에서 floodFill 시작
    for x in range(0, w - 1, 10):
        cv2.floodFill(im_floodfill, flood_mask, (x, 0), (0,))
        cv2.floodFill(im_floodfill, flood_mask, (x, h - 1), (0,))

    # 좌우측 가장자리의 10픽셀 간격에서 floodFill 실행
    for y in range(0, h - 1, 10):
        cv2.floodFill(im_floodfill, flood_mask, (0, y), (0,))
        cv2.floodFill(im_floodfill, flood_mask, (w - 1, y), (0,))

    # 확실히 가장자리 전체가 배경임을 보장 (경계 직접 0처리)
    im_floodfill[0, :] = 0
    im_floodfill[-1, :] = 0
    im_floodfill[:, 0] = 0
    im_floodfill[:, -1] = 0

    return im_floodfill


def extract_largest_contour(im_floodfill: np.ndarray, logger: Logger) -> np.ndarray:
    """
    플러드 필 결과에서 컨투어를 추출하여 가장 큰 컨투어만 남깁니다.
    이후 scipy의 binary_fill_holes을 이용해 내부의 홀을 채우고,
    최종적으로 0~255 범위의 이진 마스크를 생성하여 반환합니다.
    """
    # floodFill 결과를 반전시켜 객체 영역(원래 배경이었던 부분)을 추출
    mask2 = cv2.bitwise_not(im_floodfill)

    largest_mask = None
    largest_size = 0

    # skimage의 find_contours로 이진 이미지에서 윤곽선을 탐색 (임계값 0.0)
    contours = measure.find_contours(mask2, 0.0)

    for c in contours:
        # 탐색한 각 윤곽선을 채워서 이진 마스크 생성. 여기서는 mask2.T의 shape를 사용함.
        contour_mask = np.zeros(mask2.T.shape, np.uint8)
        cv2.fillPoly(contour_mask, [c.astype(np.int32)], (1,))
        size = np.sum(contour_mask == 1)
        if size > largest_size:
            largest_mask = contour_mask
            largest_size = size

    if largest_mask is None:
        msg = fcs.FOUND_NO_CONTOURS_WITHIN_IMAGE
        logger.critical(msg)
        raise Exception(msg)

    # 내부 홀 채우기: scipy.ndimage.binary_fill_holes -> 불리언 배열 반환
    filled_mask = ndimage.binary_fill_holes(largest_mask)

    # 최종 마스크를 0~255 범위의 uint8 이미지로 변환 후, transpose하여 반환함
    final_mask = 255 * filled_mask.astype(np.uint8) # type: ignore

    return final_mask.T


def segment_character(
    img: np.ndarray,
    logger: Logger,
):
    """
    입력 이미지로부터 문자(객체)를 추출하여 이진 마스크 형태로 반환합니다.

    전체 처리 과정:
      1. 임계값 처리 (적응형 이진화 + 반전)
      2. 형태학적 변환 (closing, dilation)
      3. 플러드 필을 통한 배경 제거
      4. 최대 컨투어 추출 및 내부 홀 채우기
    """
    # 1. 임계값 처리
    binary_img = apply_threshold(img)

    # 2. 형태학적 변환
    morph_img = apply_morphology(binary_img)

    # 3. 플러드 필을 통한 배경 제거
    floodfill_img = apply_floodfill(morph_img)

    # 4. 최대 컨투어 추출 및 내부 홀 채우기
    final_mask = extract_largest_contour(floodfill_img, logger)

    return final_mask
