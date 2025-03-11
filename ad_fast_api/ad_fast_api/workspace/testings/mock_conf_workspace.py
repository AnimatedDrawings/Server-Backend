from unittest.mock import patch
from ad_fast_api.workspace.sources import conf_workspace
from pathlib import Path


REQUEST_FILES_PATH = Path(__file__).parent.joinpath("request_files")
TMP_AD_ID = "tmp_workspace_files"
TMP_WORKSPACE_FILES = Path(__file__).parent.joinpath(TMP_AD_ID)
GARLIC_PATH = Path(__file__).parent.joinpath("garlic")
RESULT_GARLIC_AD_ID = "result_garlic"
RESULT_GARLIC_PATH = Path(__file__).parent.joinpath(RESULT_GARLIC_AD_ID)


def patcher_get_base_path(
    return_value=None,
    side_effect=None,
):
    patcher = patch.object(
        conf_workspace,
        "get_base_path",
        return_value=return_value,
        side_effect=side_effect,
    )
    return patcher
