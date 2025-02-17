from ad_fast_api.workspace.sources import work_dir


def test_get_base_path():
    ad_id = "1234567890_hexcode"
    base_path = work_dir.get_base_path(ad_id=ad_id)

    assert base_path == work_dir.FILES_PATH.joinpath(ad_id)
