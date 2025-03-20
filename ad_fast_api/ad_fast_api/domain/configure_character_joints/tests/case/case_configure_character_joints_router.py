from ad_fast_api.domain.configure_character_joints.sources.configure_character_joints_router import (
    configure_character_joints,
)
from ad_fast_api.workspace.sources import reqeust_files as rf
from ad_fast_api.domain.schema.sources.schemas import Joints
import yaml


def get_char_cfg_dict():
    char_cfg_path = rf.EXAMPLE1_DIR_PATH / rf.CHAR_CFG_YAML_FILE_NAME
    with open(char_cfg_path, "r") as f:
        char_cfg_dict = yaml.safe_load(f)
    return char_cfg_dict


def case_configure_character_joints_router():
    ad_id = rf.EXAMPLE1_AD_ID
    char_cfg_dict = get_char_cfg_dict()
    joints = Joints(**char_cfg_dict)

    response = configure_character_joints(
        ad_id=ad_id,
        joints=joints,
    )
    return response


if __name__ == "__main__":
    case_configure_character_joints_router()
