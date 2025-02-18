from unittest.mock import patch
from ad_fast_api.workspace.sources import work_dir


def patcher_get_base_path(
    return_value=None,
    side_effect=None,
):
    patcher = patch.object(
        work_dir,
        "get_base_path",
        return_value=return_value,
        side_effect=side_effect,
    )
    return patcher
