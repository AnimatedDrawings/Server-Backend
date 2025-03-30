import os
from typing import Self


FETCH_ENV_FROM_OS_ERROR = "Environment variable {env_name} is not set."


def fetch_env_from_os(
    env_name: str,
):
    env_value = os.environ.get(env_name)
    if env_value is None:
        raise Exception(
            FETCH_ENV_FROM_OS_ERROR.format(env_name=env_name),
        )
    return env_value


class ADEnv:
    internal_port: int
    animated_drawings_workspace_dir: str

    def __init__(
        self,
        internal_port: int,
        animated_drawings_workspace_dir: str,
    ):
        self.internal_port = internal_port
        self.animated_drawings_workspace_dir = animated_drawings_workspace_dir

    @classmethod
    def mock(cls) -> Self:
        return cls(
            internal_port=1234,
            animated_drawings_workspace_dir="/mock/workspace",
        )


# lazy init
_ad_env = None


def create_ad_env_instance() -> ADEnv:
    internal_port = int(fetch_env_from_os("INTERNAL_PORT"))
    animated_drawings_workspace_dir = fetch_env_from_os(
        "ANIMATED_DRAWINGS_WORKSPACE_DIR"
    )
    tmp_ad_env = ADEnv(
        internal_port=internal_port,
        animated_drawings_workspace_dir=animated_drawings_workspace_dir,
    )
    return tmp_ad_env


def get_ad_env() -> ADEnv:
    global _ad_env
    if _ad_env is None:
        _ad_env = create_ad_env_instance()
    return _ad_env
