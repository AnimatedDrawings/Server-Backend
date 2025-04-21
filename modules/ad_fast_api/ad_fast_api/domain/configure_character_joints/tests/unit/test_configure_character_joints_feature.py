from ad_fast_api.domain.configure_character_joints.sources import (
    configure_character_joints_feature as ccjf,
)
from unittest.mock import patch
from ad_fast_api.domain.schema.sources.schemas import Joints
from ad_fast_api.workspace.sources.conf_workspace import CHAR_CFG_FILE_NAME


def test_save_joints(tmp_path):
    # given
    ad_id = "dummy_ad_id"
    model_dump_return_value = {"dummy": "data"}

    # when
    with patch.object(
        Joints,
        "model_dump",
        return_value=model_dump_return_value,
    ) as mock_model_dump, patch.object(
        ccjf,
        "dict_to_file",
    ) as mock_dict_to_file, patch.object(
        ccjf,
        "get_base_path",
        return_value=tmp_path,
    ) as mock_get_base_path:
        ccjf.save_joints(
            joints=Joints.mock(),
            ad_id=ad_id,
        )

        # then
        mock_model_dump.assert_called_once_with(mode="json")
        mock_get_base_path.assert_called_once_with(ad_id=ad_id)
        mock_dict_to_file.assert_called_once_with(
            to_save_dict=model_dump_return_value,
            file_path=tmp_path.joinpath(CHAR_CFG_FILE_NAME),
        )
