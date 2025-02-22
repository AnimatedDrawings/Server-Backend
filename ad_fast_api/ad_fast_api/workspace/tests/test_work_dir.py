from ad_fast_api.workspace.sources import conf_workspace


def test_get_base_path():
    ad_id = "1234567890_hexcode"
    base_path = conf_workspace.get_base_path(ad_id=ad_id)

    assert base_path == conf_workspace.FILES_PATH.joinpath(ad_id)
