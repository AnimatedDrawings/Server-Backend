import logging
import os
from multiprocessing import Process
from zero import ZeroServer
from uuid import uuid4
from enum import Enum
from typing import TypedDict, Optional, Any, Dict


class RPCType(str, Enum):
    PING = "PING"
    RUNNING = "RUNNING"
    FULL_JOB = "FULL_JOB"
    TERMINATE = "TERMINATE"


class RPCMessage(TypedDict):
    type: RPCType
    message: Optional[str]
    data: Optional[Dict[str, Any]]


def create_rpc_message(
    type: RPCType,
    message: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """RPC 메시지를 표준 형식으로 생성합니다."""
    return {
        "type": type,
        "message": message or "",
        "data": data or {},
    }


# 전역 변수: 실행 중인 render 작업들을 저장합니다.
active_render_processes = {}
MAX_RENDER_PROCESSES = 1


def get_internal_port():
    internal_port = os.environ.get("INTERNAL_PORT")
    if internal_port is None:
        raise ValueError("INTERNAL_PORT is not set.")
    return internal_port


internal_port = get_internal_port()
app = ZeroServer(port=int(internal_port))


@app.register_rpc
def ping(n: int) -> Dict[str, Any]:
    logging.info(f"ping called with argument: {n}")

    return create_rpc_message(
        RPCType.PING,
        f"animated_drawings connection successful! Received: {n}",
    )


@app.register_rpc
def start_render(mvc_cfg_file_path: str) -> Dict[str, Any]:
    """
    클라이언트의 요청으로 render.start 작업을 별도의 프로세스로 실행합니다.
    동시에 최대 MAX_RENDER_PROCESSES개의 render 작업을 실행할 수 있습니다.
    """

    from animated_drawings import render  # type: ignore

    # 종료된 프로세스들을 정리합니다.
    finished_jobs = [
        job_id
        for job_id, proc in active_render_processes.items()
        if not proc.is_alive()
    ]
    for job_id in finished_jobs:
        del active_render_processes[job_id]

    if len(active_render_processes) >= MAX_RENDER_PROCESSES:
        message = (
            f"최대 {MAX_RENDER_PROCESSES}개의 render 작업만 동시에 실행할 수 있습니다."
        )
        logging.info(message)
        return create_rpc_message(
            RPCType.FULL_JOB,
            message,
        )

    from multiprocessing import current_process

    current_process().daemon = False

    process = Process(
        target=render.start,
        args=(mvc_cfg_file_path,),
    )
    process.start()
    job_id = str(uuid4())
    active_render_processes[job_id] = process
    logging.info(f"render 작업이 시작되었습니다. job_id: {job_id}")
    return create_rpc_message(
        RPCType.RUNNING,
        f"render 작업이 시작되었습니다. job_id: {job_id}",
        {"job_id": job_id},
    )


@app.register_rpc
def cancel_render(job_id: str) -> Dict[str, Any]:
    """
    클라이언트가 작업 중단 요청 시 호출되는 RPC 함수입니다.
    전달된 job_id에 해당하는 render 작업 프로세스를 종료합니다.
    """
    if (
        job_id not in active_render_processes
        or not active_render_processes[job_id].is_alive()
    ):
        message = f"해당 {job_id}의 실행 중인 작업이 없습니다."
        logging.info(message)
        return create_rpc_message(
            RPCType.TERMINATE,
            message,
        )

    process = active_render_processes[job_id]
    process.terminate()
    process.join()
    del active_render_processes[job_id]
    logging.info(f"job_id {job_id}의 render 프로세스가 종료되었습니다.")
    return create_rpc_message(
        RPCType.TERMINATE,
        f"job_id {job_id}의 render 프로세스가 종료되었습니다.",
    )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s"
    )
    logging.info(f"ZeroRPC server started, listening on port : {internal_port}")
    app.run(workers=1)
