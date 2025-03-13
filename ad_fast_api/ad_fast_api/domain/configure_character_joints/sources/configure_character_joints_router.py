from fastapi import APIRouter
from ad_fast_api.domain.schema.sources.joints import Joints
from ad_fast_api.domain.configure_character_joints.sources.configure_character_joints_feature import (
    save_joints,
)
from ad_fast_api.snippets.sources.ad_http_exception import handle_operation


router = APIRouter()


@router.post("/configure_character_joints")
def configure_character_joints(
    ad_id: str,
    joints: Joints,
):
    handle_operation(
        save_joints,
        joints=joints,
        ad_id=ad_id,
        status_code=500,
    )


# if __name__ == "__main__":
#     from ad_fast_api.workspace.testings import mock_conf_workspace as mcw

#     ad_id = "result_exmaple1"
#     joints = Joints(
#         joints=[],
#     )
