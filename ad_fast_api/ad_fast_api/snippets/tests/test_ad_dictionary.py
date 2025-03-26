from ad_fast_api.snippets.sources.ad_dictionary import get_value_from_dict


def test_get_value_from_dict():
    value1 = get_value_from_dict(
        ["a", "b", "c"],
        {"a": {"b": {"c": "d"}}},
    )
    value2 = get_value_from_dict(
        ["a", "b", "c"],
        {"a": {"b": {"d": "e"}}},
    )

    assert value1 == "d"
    assert value2 is None
