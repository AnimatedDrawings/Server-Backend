import os

os.environ["INTERNAL_PORT"] = "8000"

from pathlib import Path
import sys


ad_animated_drawings_path = Path(__file__).parent
animated_drawings_path = Path(__file__).parent.joinpath("AnimatedDrawings")

# 프로젝트 루트를 시스템 경로에 추가
sys.path.insert(0, str(ad_animated_drawings_path))
sys.path.insert(1, str(animated_drawings_path))

# 이제 절대 경로로 임포트 가능
from ad_animated_drawings import rpc_server
from unittest.mock import MagicMock
from unittest.mock import patch


def test_render_start_active_render_processes_is_full():
    # given
    rpc_server.active_render_processes = {
        f"dummy_id_{i}": MagicMock(
            target=lambda: None,  # 테스트용 더미 함수
            name=f"dummy_id_{i}",
        )
        for i in range(rpc_server.MAX_RENDER_PROCESSES)
    }

    # when
    result = rpc_server.start_render("dummy_path")

    # then
    assert result["status"] == "fail"
    assert result["message"] == "최대 3개의 render 작업만 동시에 실행할 수 있습니다."


@patch("animated_drawings.render.start")
def test_render_start_active_render_processes_is_not_alive(mock_render_start):
    mock_render_start.return_value = None

    # given
    rpc_server.active_render_processes = {
        f"dummy_id_{i}": MagicMock(
            target=lambda: None,  # 테스트용 더미 함수
            name=f"dummy_id_{i}",
            is_alive=lambda: False,
        )
        for i in range(rpc_server.MAX_RENDER_PROCESSES)
    }

    # when
    result = rpc_server.start_render("dummy_path")
    assert result["status"] == "success"
    assert result["message"] == "작업이 시작되었습니다."


def test_cancel_render_job_not_exists():
    # given
    job_id = "test_job_id"
    rpc_server.active_render_processes = {}

    # when
    result = rpc_server.cancel_render(job_id)

    # then
    assert result["status"] == "success"
    assert result["message"] == f"해당 {job_id}의 실행 중인 작업이 없습니다."


def test_cancel_render_job_not_alive():
    # given
    job_id = "dummy_id_1"
    mock_process = MagicMock()
    mock_process.is_alive.return_value = False
    rpc_server.active_render_processes = {job_id: mock_process}

    # when
    result = rpc_server.cancel_render(job_id)

    # then
    assert result["status"] == "success"
    assert result["message"] == f"해당 {job_id}의 실행 중인 작업이 없습니다."


def test_cancel_render_success():
    # given
    job_id = "dummy_id_1"
    mock_process = MagicMock()
    mock_process.is_alive.return_value = True
    rpc_server.active_render_processes = {job_id: mock_process}

    # when
    result = rpc_server.cancel_render(job_id)

    # then
    mock_process.terminate.assert_called_once()
    mock_process.join.assert_called_once()
    assert job_id not in rpc_server.active_render_processes
    assert result["status"] == "success"
    assert result["message"] == f"작업 {job_id}가 중단되었습니다."
