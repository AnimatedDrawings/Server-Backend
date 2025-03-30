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
from ad_animated_drawings.rpc_server import (
    RPCType,
    start_render,
)
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
    result = start_render("dummy_path")

    # then
    assert result["type"] == RPCType.FULL_JOB  # type: ignore


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
    assert result["type"] == RPCType.RUNNING  # type: ignore


def test_cancel_render_job_not_exists():
    # given
    job_id = "test_job_id"
    rpc_server.active_render_processes = {}

    # when
    result = rpc_server.cancel_render(job_id)

    # then
    assert result["type"] == RPCType.TERMINATE  # type: ignore


def test_cancel_render_job_not_alive():
    # given
    job_id = "dummy_id_1"
    mock_process = MagicMock()
    mock_process.is_alive.return_value = False
    rpc_server.active_render_processes = {job_id: mock_process}

    # when
    result = rpc_server.cancel_render(job_id)

    # then
    assert result["type"] == RPCType.TERMINATE  # type: ignore


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
    assert result["type"] == RPCType.TERMINATE  # type: ignore


def test_start_render_real_process():
    """
    실제로 프로세스를 생성하여 start_render 기능을 테스트하는 통합 테스트입니다.
    dummy_render_start 함수는 단순히 일정 시간 sleep 하도록 구현되어,
    실제 render 작업 프로세스 생성 및 등록을 확인할 수 있습니다.
    """
    from ad_animated_drawings import rpc_server
    import sys
    import types
    import time

    # dummy render 모듈 생성: 실제 render.start 함수 역할을 대신함
    dummy_render = types.ModuleType("render")

    def dummy_render_start(mvc_cfg_file_path):
        # render.start와 같이 동작: 여기서는 단순히 2초 대기
        time.sleep(2)

    dummy_render.start = dummy_render_start

    # animated_drawings.render 모듈을 dummy_render로 설정하여 실제 프로세스 생성 시 사용되도록 함
    sys.modules["animated_drawings.render"] = dummy_render

    # 활성 렌더 프로세스 초기화
    rpc_server.active_render_processes.clear()

    # when: start_render 호출 시 실제 프로세스 생성
    result = rpc_server.start_render("real_dummy_config_path")

    # then: 반환 결과가 RUNNING 타입이며, job_id가 active_render_processes에 추가되었는지 확인
    assert result["type"] == rpc_server.RPCType.RUNNING
    assert "job_id" in result["data"]
    job_id = result["data"]["job_id"]
    assert job_id in rpc_server.active_render_processes
    process = rpc_server.active_render_processes[job_id]
    assert process.is_alive()

    # 테스트 완료 후 생성된 프로세스 정리
    process.terminate()
    process.join()

    # dummy 모듈 제거
    del sys.modules["animated_drawings.render"]


def test_start_render_multiple_processes():
    """
    실제로 여러 render 프로세스를 생성하여 최대 프로세스 제한과 초과 시의 동작을 확인하는 통합 테스트입니다.
    MAX_RENDER_PROCESSES 개수까지는 프로세스 생성이 정상적으로 이뤄지고,
    그 이후 추가 생성 요청 시 FULL_JOB 타입의 메시지가 반환되는지 확인합니다.
    """
    from ad_animated_drawings import rpc_server
    import sys
    import types
    import time

    # dummy render 모듈 생성: 실제 render.start 함수 역할을 대신함
    dummy_render = types.ModuleType("render")

    def dummy_render_start(mvc_cfg_file_path):
        # render.start와 같이 동작: 여기서는 단순히 5초 대기하여 프로세스가 살아있음을 유지
        time.sleep(5)

    dummy_render.start = dummy_render_start

    # animated_drawings.render 모듈을 dummy_render로 설정 (테스트 동안 사용)
    sys.modules["animated_drawings.render"] = dummy_render

    # 활성 render 프로세스 초기화
    rpc_server.active_render_processes.clear()

    running_job_ids = []
    # 최대 개수까지 프로세스를 생성합니다.
    for i in range(rpc_server.MAX_RENDER_PROCESSES):
        result = rpc_server.start_render(f"dummy_config_path_{i}")
        assert result["type"] == rpc_server.RPCType.RUNNING
        assert "job_id" in result["data"]
        job_id = result["data"]["job_id"]
        running_job_ids.append(job_id)
        assert job_id in rpc_server.active_render_processes
        process = rpc_server.active_render_processes[job_id]
        assert process.is_alive()

    # 현재 활성화된 프로세스 수가 MAX_RENDER_PROCESSES와 동일해야 합니다.
    assert len(rpc_server.active_render_processes) == rpc_server.MAX_RENDER_PROCESSES

    # 추가로 render 프로세스 생성 요청 시, MAX_RENDER_PROCESSES 초과로 FULL_JOB 메시지가 반환되어야 함.
    result = rpc_server.start_render("dummy_config_path_overflow")
    assert result["type"] == rpc_server.RPCType.FULL_JOB

    # 테스트 완료 후 생성된 프로세스 정리
    for job_id in running_job_ids:
        if job_id in rpc_server.active_render_processes:
            process = rpc_server.active_render_processes[job_id]
            process.terminate()
            process.join()

    # dummy 모듈 제거
    del sys.modules["animated_drawings.render"]
