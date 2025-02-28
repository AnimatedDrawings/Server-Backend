from ad_fast_api.domain.make_animation.sources.make_animation_schema import (
    ADAnimation,
)
from ad_fast_api.domain.make_animation.sources.errors.make_animation_400_status import (
    INVALID_ANIMATION,
)
from ad_fast_api.workspace.sources.conf_workspace import (
    get_video_dir_path,
    get_video_file_name,
)
from pathlib import Path
from typing import Optional


def check_available_animation(ad_animation: str):
    if not ad_animation in ADAnimation:
        raise INVALID_ANIMATION


def is_video_file_exists(
    base_path: Path,
    ad_animation: str,
) -> Optional[Path]:
    video_dir_path = get_video_dir_path(
        base_path=base_path,
    )
    video_dir_path.mkdir(exist_ok=True)
    video_file_name = get_video_file_name(ad_animation)
    video_file_path = video_dir_path.joinpath(video_file_name)

    # /video/dab.gif
    relative_video_file_path = video_file_path.relative_to(base_path)

    if video_file_path.exists():
        return None
    else:
        return relative_video_file_path
