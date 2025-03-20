from ad_fast_api.workspace.sources import reqeust_files as rf
from ad_fast_api.workspace.sources import conf_workspace as cw
from ad_fast_api.snippets.sources.ad_logger import setup_logger
from ad_fast_api.domain.cutout_character.sources.features import configure_skeleton
from ad_fast_api.domain.cutout_character.testings.mock_configure_skeleton import (
    mock_pose_results,
    mock_kpts,
)


async def case_get_pose_result_async():
    base_path = cw.get_base_path(ad_id=rf.EXAMPLE1_AD_ID)
    logger = setup_logger(base_path=base_path)

    cropped_image = configure_skeleton.get_cropped_image(
        base_path=base_path,
        logger=logger,
    )

    url = "http://localhost:8080/predictions/drawn_humanoid_pose_estimator"
    response = await configure_skeleton.get_pose_result_async(
        cropped_image=cropped_image,
        logger=logger,
        url=url,
    )

    return response


def case_create_char_cfg_dict():
    base_path = cw.get_base_path(ad_id=rf.EXAMPLE1_AD_ID)
    mock_logger = setup_logger(base_path=base_path)
    cropped_image = configure_skeleton.get_cropped_image(
        base_path=base_path,
        logger=mock_logger,
    )

    kpts = configure_skeleton.check_pose_results(
        pose_results=mock_pose_results,
        logger=mock_logger,
    )

    skeleton = configure_skeleton.make_skeleton(
        kpts=kpts,
    )

    char_cfg_dict = configure_skeleton.save_char_cfg(
        skeleton=skeleton,
        cropped_image=cropped_image,
        base_path=base_path,
    )

    return char_cfg_dict


if __name__ == "__main__":
    import asyncio

    response = asyncio.run(case_get_pose_result_async())
    print(response)
