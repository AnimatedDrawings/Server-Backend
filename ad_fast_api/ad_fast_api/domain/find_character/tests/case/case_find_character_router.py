from ad_fast_api.domain.find_character.sources.find_character_router import (
    find_character,
)
from ad_fast_api.workspace.sources import reqeust_files
from ad_fast_api.domain.schema.sources.schemas import BoundingBox
import yaml


def get_sample1_bounding_box_dict():
    bounding_box_path = (
        reqeust_files.EXAMPLE1_DIR_PATH / reqeust_files.BOUNDING_BOX_FILE_NAME
    )
    with open(bounding_box_path, "r") as f:
        bounding_box = yaml.safe_load(f)
    return bounding_box


def case_find_character_router():
    ad_id = reqeust_files.EXAMPLE1_AD_ID
    bounding_box_dict = get_sample1_bounding_box_dict()
    bounding_box = BoundingBox(**bounding_box_dict)

    response = find_character(ad_id=ad_id, bounding_box=bounding_box)
    return response


if __name__ == "__main__":
    response = case_find_character_router()
    print(response)
