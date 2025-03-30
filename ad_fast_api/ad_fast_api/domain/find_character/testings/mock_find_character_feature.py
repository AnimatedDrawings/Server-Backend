from unittest.mock import patch
from ad_fast_api.domain.find_character.sources.features import (
    find_character_feature as fcf,
)


def patcher_crop_and_segment_character(
    return_value=None,
    side_effect=None,
):
    patcher = patch.object(
        fcf,
        "crop_and_segment_character",
        return_value=return_value,
        side_effect=side_effect,
    )
    return patcher
