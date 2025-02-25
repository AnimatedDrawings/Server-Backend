from ad_fast_api.domain.schema.sources.joints import Joints
from ad_fast_api.snippets.sources.save_dict import dict_to_file
from ad_fast_api.workspace.sources.conf_workspace import (
    get_base_path,
    CHAR_CFG_FILE_NAME,
)


def save_joints(
    ad_id: str,
    joints: Joints,
):
    to_save_dict = joints.model_dump(mode="json")
    base_path = get_base_path(ad_id=ad_id)
    char_cfg_path = base_path.joinpath(CHAR_CFG_FILE_NAME)
    dict_to_file(
        to_save_dict=to_save_dict,
        file_path=char_cfg_path,
    )
