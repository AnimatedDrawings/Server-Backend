import asyncio
from unittest.mock import patch
from ad_fast_api.workspace.testings.mock_conf_workspace import (
    RESULT_GARLIC_PATH,
    RESULT_GARLIC_AD_ID,
)
from ad_fast_api.workspace.sources.conf_workspace import get_base_path
from ad_fast_api.domain.make_animation.sources.features import (
    make_animation_feature as maf,
)
from ad_fast_api.domain.make_animation.sources.make_animation_schema import (
    ADAnimation,
)
from ad_fast_api.snippets.sources.ad_env import ADEnv


def make_animation_garlic():
    ad_id = "result_garlic"
    base_path = get_base_path(ad_id=ad_id)
    ad_animation = ADAnimation.dab.value

    relative_video_file_path = maf.check_make_animation_info(
        base_path=base_path,
        ad_animation=ad_animation,
    )

    if relative_video_file_path is None:
        print("video file exists.. not making animation")
        return

    with patch.object(
        maf,
        "get_ad_env",
        return_value=ADEnv.mock(),
    ):
        mvc_cfg_path = maf.prepare_make_animation(
            ad_id=ad_id,
            base_path=base_path,
            ad_animation=ad_animation,
            relative_video_file_path=relative_video_file_path,
        )

        # maf.image_to_animation(
        #     animated_drawings_mvc_cfg_path=mvc_cfg_path,
        # )

    # 필요에 따라 추가 assert 검증 가능
    # assert mvc_cfg_path.exists(), "MVC config file should be created"


if __name__ == "__main__":
    make_animation_garlic()
