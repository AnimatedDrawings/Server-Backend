from ad_fast_api.domain.make_animation.sources.make_animation_router import (
    make_animation,
)
from ad_fast_api.workspace.sources import reqeust_files as rf
import shutil
from ad_fast_api.workspace.sources import conf_workspace as cw


def remove_result_video_files(ad_id: str):
    tmp_base_path = cw.get_base_path(ad_id=ad_id)
    video_dir_path = cw.get_video_dir_path(base_path=tmp_base_path)
    shutil.rmtree(video_dir_path)


async def case_make_animation_router(ad_id: str):
    ad_animation = "dab"

    response = await make_animation(
        ad_id=ad_id,
        ad_animation=ad_animation,
    )
    return response


if __name__ == "__main__":
    import asyncio
    from unittest.mock import patch
    from ad_fast_api.domain.make_animation.sources.features import image_to_animation
    from ad_fast_api.snippets.sources import ad_env
    from ad_fast_api.snippets.sources.ad_env import ADEnv

    mock_zero_client = image_to_animation.get_zero_client(
        host="localhost",
        timeout=60 * 1000,
    )
    mock_ad_env = ADEnv(
        internal_port=8001,
        animated_drawings_workspace_dir="workspace",
    )
    ad_id = rf.EXAMPLE1_AD_ID

    with patch.object(
        image_to_animation,
        "get_zero_client",
        return_value=mock_zero_client,
    ), patch.object(
        ad_env,
        "_ad_env",
        new=mock_ad_env,
    ):
        asyncio.run(
            case_make_animation_router(ad_id=ad_id),
        )

    remove_result_video_files(ad_id=ad_id)
