import logging
import os
from collections import deque
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


active_render_processes = {}  # 실행 중인 render 작업들을 저장합니다.
MAX_RENDER_PROCESSES = 1
render_job_queue = deque()  # 대기열을 위한 변수
MAX_RENDER_QUEUE_LENGTH = 4
on_running_render_job_ids = set()


def process_queue():
    """대기열에 있는 작업들을 활성화 가능한 슬롯이 있을 때 실행합니다."""
    from animated_drawings import render  # type: ignore

    while len(active_render_processes) < MAX_RENDER_PROCESSES and render_job_queue:
        job = render_job_queue.popleft()
        process = Process(
            target=render.start,
            args=(job["mvc_cfg_file_path"],),
        )
        process.start()
        job_id = job["job_id"]
        active_render_processes[job_id] = process
        on_running_render_job_ids.add(job_id)
        logging.info(f"대기열에서 render 작업을 시작하였습니다. job_id: {job_id}")


def clean_finished_jobs():
    finished_jobs = [
        job_id
        for job_id, proc in active_render_processes.items()
        if not proc.is_alive()
    ]
    for job_id in finished_jobs:
        del active_render_processes[job_id]
        on_running_render_job_ids.remove(job_id)
    process_queue()


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

    clean_finished_jobs()

    if len(active_render_processes) < MAX_RENDER_PROCESSES:
        from multiprocessing import current_process

        current_process().daemon = False
        process = Process(
            target=render.start,
            args=(mvc_cfg_file_path,),
        )
        process.start()
        job_id = str(uuid4())
        active_render_processes[job_id] = process
        on_running_render_job_ids.add(job_id)
        logging.info(f"render 작업이 시작되었습니다. job_id: {job_id}")
        return create_rpc_message(
            RPCType.RUNNING,
            f"render 작업이 시작되었습니다. job_id: {job_id}",
            {"job_id": job_id},
        )
    else:
        if len(render_job_queue) < MAX_RENDER_QUEUE_LENGTH:
            job_id = str(uuid4())
            render_job_queue.append(
                {
                    "job_id": job_id,
                    "mvc_cfg_file_path": mvc_cfg_file_path,
                }
            )
            on_running_render_job_ids.add(job_id)
            message = f"모든 render 작업이 사용중입니다. 작업이 대기열에 추가되었습니다. 현재 대기열 길이: {len(render_job_queue)}"
            logging.info(message)
            return create_rpc_message(
                RPCType.RUNNING,
                message,
                {
                    "job_id": job_id,
                    "queue_position": len(render_job_queue),
                },
            )
        else:
            message = f"대기열이 가득 찼습니다. 최대 {MAX_RENDER_QUEUE_LENGTH}개의 대기열만 허용됩니다."
            logging.info(message)
            return create_rpc_message(
                RPCType.FULL_JOB,
                message,
            )


@app.register_rpc
def cancel_render(job_id: str) -> Dict[str, Any]:
    """
    클라이언트가 작업 중단 요청 시 호출되는 RPC 함수입니다.
    전달된 job_id에 해당하는 render 작업 프로세스를 종료합니다.
    """
    if job_id not in on_running_render_job_ids:
        message = f"해당 {job_id}의 실행 중인 작업이 없습니다."
        logging.info(message)
        return create_rpc_message(
            RPCType.TERMINATE,
            message,
        )

    if job_id in active_render_processes:
        process = active_render_processes[job_id]
        process.terminate()
        process.join()
        del active_render_processes[job_id]
    else:
        for idx in range(len(render_job_queue)):
            if render_job_queue[idx]["job_id"] == job_id:
                del render_job_queue[idx]
                break

    on_running_render_job_ids.remove(job_id)
    logging.info(f"job_id {job_id}의 render 프로세스가 종료되었습니다.")
    process_queue()
    return create_rpc_message(
        RPCType.TERMINATE,
        f"job_id {job_id}의 render 프로세스가 종료되었습니다.",
    )


@app.register_rpc
def is_finish_render(job_id: str) -> Dict[str, Any]:
    """
    클라이언트가 작업 완료 여부를 확인하기 위해 호출되는 RPC 함수입니다.
    전달된 job_id에 해당하는 render 작업 프로세스가 종료되었는지 확인합니다.
    """

    clean_finished_jobs()

    if job_id not in on_running_render_job_ids:
        msg = f"job_id {job_id}의 render 작업이 완료되었습니다"
        logging.info(msg)
        return create_rpc_message(
            RPCType.TERMINATE,
            msg,
        )
    else:
        msg = f"job_id {job_id}의 render 작업이 진행중입니다"
        logging.info(msg)
        return create_rpc_message(
            RPCType.RUNNING,
            msg,
        )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s"
    )
    logging.info(f"ZeroRPC server started, listening on port : {internal_port}")
    app.run(workers=1)
