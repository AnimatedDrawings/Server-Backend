import json
from pathlib import Path

import cv2
import httpx
import numpy as np
import pytest

# 테스트 대상 모듈 import
from ad_fast_api.domain.cutout_character.sources.features import (
    configure_skeleton as cs,
)
from ad_fast_api.workspace.sources.conf_workspace import CHAR_CFG_FILE_NAME
from ad_fast_api.snippets.testings.mock_logger import mock_logger
from ad_fast_api.domain.cutout_character.sources.errors import (
    cutout_character_500_status as cc5s,
)


# -------------------------------
# get_pose_result_async 함수 테스트
# -------------------------------
@pytest.mark.asyncio
async def test_get_pose_result_async_success(monkeypatch, mock_logger):
    # 더미 이미지 생성
    cropped_image = np.zeros((10, 10, 3), dtype=np.uint8)
    dummy_result = [{"keypoints": [[float(i), float(i)] for i in range(17)]}]

    # 비동기 HTTP 클라이언트 Dummy 클래스 정의
    class DummyAsyncClient:
        async def post(self, url, files):
            # 올바른 응답 코드와 JSON 컨텐츠 생성
            content = json.dumps(dummy_result).encode()
            return httpx.Response(status_code=200, content=content)

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, tb):
            pass

    def dummy_async_client(*args, **kwargs):
        return DummyAsyncClient()

    monkeypatch.setattr(httpx, "AsyncClient", dummy_async_client)
    result = await cs.get_pose_result_async(
        cropped_image=cropped_image,
        logger=mock_logger,
    )
    expected_result = dummy_result
    assert result == expected_result


@pytest.mark.asyncio
async def test_get_pose_result_async_exception_in_post(monkeypatch, mock_logger):
    cropped_image = np.zeros((10, 10, 3), dtype=np.uint8)
    post_error_msg = "test error"

    class DummyAsyncClient:
        async def post(self, url, files):
            raise Exception(post_error_msg)

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, tb):
            pass

    def dummy_async_client(*args, **kwargs):
        return DummyAsyncClient()

    monkeypatch.setattr(httpx, "AsyncClient", dummy_async_client)
    with pytest.raises(Exception) as excinfo:
        await cs.get_pose_result_async(cropped_image, mock_logger)

    expect_msg = cc5s.GET_SKELETON_TORCHSERVE_ERROR.format(resp=post_error_msg)
    assert str(excinfo.value) == expect_msg
    mock_logger.critical.assert_called_once_with(expect_msg)


@pytest.mark.asyncio
async def test_get_pose_result_async_http_error_status(monkeypatch, mock_logger):
    cropped_image = np.zeros((10, 10, 3), dtype=np.uint8)
    dummy_response = httpx.Response(status_code=400, content=b"Error")

    class DummyAsyncClient:
        async def post(self, url, files):
            return dummy_response

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, tb):
            pass

    def dummy_async_client(*args, **kwargs):
        return DummyAsyncClient()

    monkeypatch.setattr(httpx, "AsyncClient", dummy_async_client)
    with pytest.raises(Exception) as excinfo:
        await cs.get_pose_result_async(
            cropped_image=cropped_image,
            logger=mock_logger,
        )

    expect_msg = cc5s.GET_SKELETON_TORCHSERVE_ERROR.format(resp=dummy_response)
    assert str(excinfo.value) == expect_msg
    mock_logger.critical.assert_called_once_with(expect_msg)


# -------------------------------
# check_pose_results 함수 테스트
# -------------------------------
def test_check_pose_results_error_code_404(mock_logger):
    # given
    # pose_results가 dict 형태로 "code":404 인 경우
    pose_results = {"code": 404, "error": "not found"}

    # when
    with pytest.raises(Exception) as excinfo:
        cs.check_pose_results(
            pose_results=pose_results,  # type: ignore
            logger=mock_logger,
        )

    # then
    expect_msg = cc5s.POSE_ESTIMATION_ERROR.format(pose_results=pose_results)
    assert str(excinfo.value) == expect_msg
    mock_logger.critical.assert_called_once_with(expect_msg)


def test_check_pose_results_empty(mock_logger):
    # given
    # 빈 리스트 전달 시, skeleton이 검출되지 않은 것으로 처리되어 Exception 발생
    pose_results = []

    # when
    with pytest.raises(Exception) as excinfo:
        cs.check_pose_results(
            pose_results=pose_results,
            logger=mock_logger,
        )

    # then
    expect_msg = cc5s.NO_SKELETON_DETECTED
    assert str(excinfo.value) == expect_msg
    mock_logger.critical.assert_called_once_with(expect_msg)


def test_check_pose_results_more_than_one(mock_logger):
    # given
    # skeleton이 2개 이상 감지된 경우 예외 발생
    valid_pose_value = [[float(i), float(i)] for i in range(17)]
    valid_pose = {"keypoints": valid_pose_value}
    pose_results = [valid_pose, valid_pose]

    # when
    with pytest.raises(Exception) as excinfo:
        cs.check_pose_results(
            pose_results=pose_results,
            logger=mock_logger,
        )

    # then
    expect_msg = cc5s.MORE_THAN_ONE_SKELETON_DETECTED.format(
        len_pose_results=len(pose_results)
    )
    assert str(excinfo.value) == expect_msg
    mock_logger.critical.assert_called_once_with(expect_msg)


def test_check_pose_results_valid(mock_logger):
    # 올바른 pose_results 케이스: 리스트에 1개의 dict, key "keypoints" 존재
    # given
    keypoints_value = [[float(i), float(i + 0.5)] for i in range(17)]
    pose_results = [{"keypoints": keypoints_value}]

    # when
    result = cs.check_pose_results(
        pose_results=pose_results,
        logger=mock_logger,
    )

    # then
    expected = np.array(pose_results[0]["keypoints"])[:, :2]
    np.testing.assert_array_equal(result, expected)


# -------------------------------
# make_skeleton 함수 테스트
# -------------------------------
def test_make_skeleton():
    # given
    # kpts: (17, 2) numpy array 예시
    kpts = np.array([[i, i + 1] for i in range(17)], dtype=float)

    # when
    skeleton = cs.make_skeleton(kpts)

    # then
    # skeleton 리스트 길이 및 첫 번째 항목("root") 검증
    assert isinstance(skeleton, list)
    assert len(skeleton) == 16
    expected_root = [round(x) for x in ((kpts[11] + kpts[12]) / 2)]
    assert skeleton[0]["name"] == "root"
    assert skeleton[0]["loc"] == expected_root


# -------------------------------
# save_char_cfg 함수 테스트
# -------------------------------
def test_save_char_cfg(tmp_path, monkeypatch):
    # given
    # 임의의 skeleton과 cropped_image 생성
    skeleton = [{"name": "test", "loc": [0, 0], "parent": None}]
    cropped_image = np.zeros((50, 100, 3), dtype=np.uint8)
    base_path = tmp_path
    recorded = {}

    # dict_to_file를 Dummy 함수로 덮어써서 전달값을 record
    def dummy_dict_to_file(to_save_dict, file_path):
        recorded["to_save_dict"] = to_save_dict
        recorded["file_path"] = file_path

    # when
    monkeypatch.setattr(cs, "dict_to_file", dummy_dict_to_file)
    cs.save_char_cfg(skeleton, cropped_image, base_path)
    expected_file_path = base_path / CHAR_CFG_FILE_NAME

    # then
    # 저장된 파일 경로 및 설정값 검증
    assert recorded["file_path"] == expected_file_path
    char_cfg = recorded["to_save_dict"]
    assert char_cfg["skeleton"] == skeleton
    assert char_cfg["height"] == 50
    assert char_cfg["width"] == 100
