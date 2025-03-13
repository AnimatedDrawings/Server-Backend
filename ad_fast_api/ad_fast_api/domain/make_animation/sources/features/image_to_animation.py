from pathlib import Path
from zero import AsyncZeroClient


# internal port env 사용하기
def get_zero_client(
    host: str = "animated_drawings",
    port: int = 8001,
    timeout: int = 2000,
):
    zero_client = AsyncZeroClient(
        host,
        port,
        default_timeout=timeout,
    )
    return zero_client


async def render_start_async(
    animated_drawings_mvc_cfg_path: Path,
    timeout: int = 60 * 1000,
):
    response = await get_zero_client(timeout=timeout).call(
        "render_start",
        animated_drawings_mvc_cfg_path.as_posix(),
    )

    status = "status"
    if response is None or status not in response:
        raise Exception("애니메이션 렌더링에 실패, 알수없는 리턴값입니다.")

    if response[status] == "success":
        return

    if response[status] == "fail":
        error_message = response["message"]
        print(error_message)
        raise Exception(error_message)
