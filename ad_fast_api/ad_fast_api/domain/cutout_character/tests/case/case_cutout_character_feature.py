from ad_fast_api.domain.cutout_character.sources.features import (
    cutout_character_feature,
)
from ad_fast_api.domain.cutout_character.testings.mock_configure_skeleton import (
    mock_char_cfg_dict,
)


def case_create_cutout_character_response():
    char_cfg_dict = cutout_character_feature.create_cutout_character_response(
        char_cfg_dict=mock_char_cfg_dict,
    )

    return char_cfg_dict


if __name__ == "__main__":
    response = case_create_cutout_character_response()
    print(response)
