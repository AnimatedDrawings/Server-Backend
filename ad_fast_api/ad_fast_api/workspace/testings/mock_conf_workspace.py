from unittest.mock import patch
from ad_fast_api.workspace.sources import conf_workspace
from pathlib import Path


GARLIC_PATH = Path(__file__).parent.joinpath("garlic")
GARLIC_TEST_PATH = Path(__file__).parent.joinpath("garlic_test")


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
