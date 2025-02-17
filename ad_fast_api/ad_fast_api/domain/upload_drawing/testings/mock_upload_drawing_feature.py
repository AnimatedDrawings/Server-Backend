from unittest.mock import patch
from ad_fast_api.domain.upload_drawing.sources.features import configure_work_dir as cwd


def patcher_make_ad_id(
    return_value=None,
    side_effect=None,
):
    patcher = patch.object(
        cwd,
        "make_ad_id",
        return_value=return_value,
        side_effect=side_effect,
    )
    return patcher


def patcher_create_base_dir(
    return_value=None,
    side_effect=None,
):
    patcher = patch.object(
        cwd,
        "create_base_dir",
        return_value=return_value,
        side_effect=side_effect,
    )
    return patcher


def patcher_get_file_bytes(
    return_value=None,
    side_effect=None,
):
    patcher = patch.object(
        cwd,
        "get_file_bytes",
        return_value=return_value,
        side_effect=side_effect,
    )
    return patcher


def patcher_save_origin_image(
    return_value=None,
    side_effect=None,
):
    patcher = patch.object(
        cwd,
        "save_origin_image",
        return_value=return_value,
        side_effect=side_effect,
    )
    return patcher


def patcher_save_image(
    return_value=None,
    side_effect=None,
):
    patcher = patch.object(
        cwd,
        "save_image",
        return_value=return_value,
        side_effect=side_effect,
    )
    return patcher
