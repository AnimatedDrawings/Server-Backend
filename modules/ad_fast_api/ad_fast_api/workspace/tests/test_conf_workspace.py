from ad_fast_api.workspace.sources import conf_workspace


def test_get_base_path():
    ad_id = "1234567890_hexcode"
    base_path = conf_workspace.get_base_path(ad_id=ad_id)

    assert base_path == conf_workspace.FILES_PATH.joinpath(ad_id)


def test_get_video_file_name():
    # given
    ad_animation = "sample_animation"
    expected = "sample_animation.gif"

    # when
    result = conf_workspace.get_video_file_name(ad_animation)

    # then
    assert result == expected, f"Expected {expected}, got {result}"


def test_get_video_dir_path(tmp_path):
    # given
    expected = tmp_path.joinpath(conf_workspace.VIDEO_DIR_NAME)

    # when
    result = conf_workspace.get_video_dir_path(base_path=tmp_path)

    # then
    assert result == expected, f"Expected {expected}, got {result}"
