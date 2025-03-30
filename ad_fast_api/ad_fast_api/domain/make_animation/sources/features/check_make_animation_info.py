from ad_fast_api.domain.make_animation.sources.make_animation_schema import (
    ADAnimation,
)
from ad_fast_api.workspace.sources.conf_workspace import (
    get_video_dir_path,
    get_video_file_name,
)
from pathlib import Path
from typing import Tuple
from logging import Logger


def check_available_animation(ad_animation: str, logger: Logger):
    if not ad_animation in ADAnimation:
        msg = "Invalid animation. Please check the animation name."
        logger.error(msg)
        raise Exception(msg)


def get_video_file_path(
    base_path: Path,
    ad_animation: str,
    logger: Logger,
) -> Tuple[Path, Path]:
    video_dir_path = get_video_dir_path(
        base_path=base_path,
    )
    video_dir_path.mkdir(exist_ok=True)
    video_file_name = get_video_file_name(ad_animation)
    video_file_path = video_dir_path.joinpath(video_file_name)
    # /video/dab.gif
    relative_video_file_path = video_file_path.relative_to(base_path)

    is_exist = video_file_path.exists()
    if is_exist:
        msg = f"Animation file exists: {video_file_path}"
        logger.info(msg)

    return (video_file_path, relative_video_file_path)
