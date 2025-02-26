from pathlib import Path
from typing import Optional
from ad_fast_api.domain.make_animation.sources.features.check_make_animation_info import (
    check_available_animation,
    is_video_file_exists,
)
from ad_fast_api.domain.make_animation.sources.features.prepare_make_animation import (
    create_animated_drawing_dict,
    create_mvc_config,
    save_mvc_config,
)


def check_make_animation_info(
    base_path: Path,
    ad_animation: str,
) -> Optional[Path]:
    check_available_animation(
        ad_animation=ad_animation,
    )
    is_exist = is_video_file_exists(
        base_path=base_path,
        ad_animation=ad_animation,
    )
    return is_exist


def prepare_make_animation(
    base_path: Path,
    ad_animation: str,
    video_file_path: Path,
) -> Path:
    animated_drawing_dict = create_animated_drawing_dict(
        base_path=base_path,
        ad_animation=ad_animation,
    )
    mvc_cfg = create_mvc_config(
        animated_drawing_dict=animated_drawing_dict,
        video_file_path=video_file_path,
    )
    mvc_cfg_path = save_mvc_config(
        mvc_cfg=mvc_cfg,
        base_path=base_path,
    )

    return mvc_cfg_path


def image_to_animation(
    mvc_cfg_path: Path,
):
    pass
