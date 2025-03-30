from unittest.mock import patch, Mock
from ad_fast_api.domain.find_character.sources import find_character_router


def patcher_save_bounding_box(
    return_value=None,
    side_effect=None,
):
    patcher = patch.object(
        find_character_router,
        "save_bounding_box",
        return_value=return_value,
        side_effect=side_effect,
    )
    return patcher


def patcher_setup_logger(
    return_value=Mock(),
    side_effect=None,
):
    patcher = patch.object(
        find_character_router,
        "setup_logger",
        return_value=return_value,
        side_effect=side_effect,
    )
    return patcher
