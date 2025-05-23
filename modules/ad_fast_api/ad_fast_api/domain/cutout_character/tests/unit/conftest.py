import numpy as np
import pytest
from fastapi.testclient import TestClient
from ad_fast_api.main import app


@pytest.fixture(scope="session")
def mock_client():
    return TestClient(app)


@pytest.fixture
def sample_image():
    # 간단한 테스트 이미지 생성 (100x100 크기의 검은색 이미지)
    return np.zeros((100, 100, 3), dtype=np.uint8)


@pytest.fixture
def sample_pose_results():
    # 샘플 포즈 결과 데이터
    return [
        {
            "keypoints": [
                [50, 10, 0.9],  # 0: 목
                [0, 0, 0],  # 1: 사용 안 함
                [0, 0, 0],  # 2: 사용 안 함
                [0, 0, 0],  # 3: 사용 안 함
                [0, 0, 0],  # 4: 사용 안 함
                [40, 30, 0.8],  # 5: 왼쪽 어깨
                [60, 30, 0.8],  # 6: 오른쪽 어깨
                [30, 50, 0.7],  # 7: 왼쪽 팔꿈치
                [70, 50, 0.7],  # 8: 오른쪽 팔꿈치
                [20, 70, 0.6],  # 9: 왼쪽 손
                [80, 70, 0.6],  # 10: 오른쪽 손
                [45, 60, 0.9],  # 11: 왼쪽 엉덩이
                [55, 60, 0.9],  # 12: 오른쪽 엉덩이
                [40, 80, 0.8],  # 13: 왼쪽 무릎
                [60, 80, 0.8],  # 14: 오른쪽 무릎
                [35, 95, 0.7],  # 15: 왼쪽 발
                [65, 95, 0.7],  # 16: 오른쪽 발
            ]
        }
    ]
