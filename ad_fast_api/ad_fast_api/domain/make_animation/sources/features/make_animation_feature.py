from pathlib import Path
from typing import Tuple
from ad_fast_api.domain.make_animation.sources.features.check_make_animation_info import (
    check_available_animation,
    is_video_file_exists,
)
from ad_fast_api.domain.make_animation.sources.features.prepare_make_animation import (
    create_animated_drawing_dict,
    create_mvc_config,
    save_mvc_config,
)
from ad_fast_api.domain.make_animation.sources.features.image_to_animation import (
    render_start_async,
)
from ad_fast_api.snippets.sources.ad_env import get_ad_env
from ad_fast_api.workspace.sources.conf_workspace import (
    FILES_DIR_NAME,
    MVC_CFG_FILE_NAME,
)
from fastapi.responses import FileResponse
from ad_fast_api.domain.make_animation.sources.errors.make_animation_500_status import (
    NOT_FOUND_ANIMATION_FILE,
)


def get_file_response(
    base_path: Path,
    relative_video_file_path: Path,
) -> FileResponse:
    video_file_path = base_path.joinpath(relative_video_file_path)
    file_response = FileResponse(
        video_file_path.as_posix(),
        media_type="image/gif",
    )
    return file_response


def check_make_animation_info(
    base_path: Path,
    ad_animation: str,
) -> Tuple[bool, Path]:
    check_available_animation(
        ad_animation=ad_animation,
    )
    return is_video_file_exists(
        base_path=base_path,
        ad_animation=ad_animation,
    )


def prepare_make_animation(
    ad_id: str,
    base_path: Path,
    ad_animation: str,
    relative_video_file_path: Path,
) -> Path:
    animated_drawings_workspace_path = Path(
        get_ad_env().animated_drawings_workspace_dir
    )
    animated_drawings_base_path = animated_drawings_workspace_path.joinpath(
        FILES_DIR_NAME
    ).joinpath(ad_id)

    animated_drawings_dict = create_animated_drawing_dict(
        animated_drawings_base_path=animated_drawings_base_path,
        animated_drawings_workspace_path=animated_drawings_workspace_path,
        ad_animation=ad_animation,
    )

    video_file_path = animated_drawings_base_path.joinpath(relative_video_file_path)

    mvc_cfg_dict = create_mvc_config(
        animated_drawings_dict=animated_drawings_dict,
        video_file_path=video_file_path,
    )
    save_mvc_config(
        mvc_cfg_file_name=MVC_CFG_FILE_NAME,
        mvc_cfg_dict=mvc_cfg_dict,
        base_path=base_path,
    )

    animated_drawings_mvc_cfg_path = animated_drawings_base_path.joinpath(
        MVC_CFG_FILE_NAME
    )
    return animated_drawings_mvc_cfg_path


async def image_to_animation_async(
    base_path: Path,
    animated_drawings_mvc_cfg_path: Path,
    relative_video_file_path: Path,
) -> FileResponse:
    await render_start_async(
        animated_drawings_mvc_cfg_path=animated_drawings_mvc_cfg_path,
    )

    video_file_path = base_path.joinpath(relative_video_file_path)
    if not video_file_path.exists():
        raise NOT_FOUND_ANIMATION_FILE

    file_response = get_file_response(
        base_path=base_path,
        relative_video_file_path=relative_video_file_path,
    )
    return file_response
