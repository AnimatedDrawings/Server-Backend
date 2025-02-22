from unittest.mock import patch
from ad_fast_api.domain.ad_features.sources import bounding_box_feature


def patcher_save_bounding_box(
    return_value=None,
    side_effect=None,
):
    patcher = patch.object(
        bounding_box_feature,
        "save_bounding_box",
        return_value=return_value,
        side_effect=side_effect,
    )
    return patcher
