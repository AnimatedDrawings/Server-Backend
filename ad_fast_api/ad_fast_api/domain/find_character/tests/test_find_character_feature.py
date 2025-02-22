from ad_fast_api.domain.find_character.sources.features import (
    find_character_feature as fcf,
)
from ad_fast_api.snippets.testings.ad_test.mock_ad_numpy import (
    sample_image_100x100_rgb,
)
from ad_fast_api.workspace.sources import conf_workspace as cw
from ad_fast_api.workspace.testings import mock_conf_workspace as mcw
import yaml
from ad_fast_api.domain.schema.sources.schemas import BoundingBox
from ad_fast_api.snippets.sources.ad_logger import setup_logger


def test_cv2_save_image(sample_image_100x100_rgb, tmp_path):
    image_name = "test.png"
    fcf.cv2_save_image(sample_image_100x100_rgb, image_name, tmp_path)
    assert tmp_path.joinpath(image_name).exists()


if __name__ == "__main__":
    logger = setup_logger(base_path=mcw.GARLIC_TEST_PATH)
    bounding_box_path = mcw.GARLIC_PATH.joinpath(cw.BOUNDING_BOX_FILE_NAME)

    with open(bounding_box_path, "r", encoding="utf-8") as file:
        bounding_box_dict = yaml.safe_load(file)
        bounding_box = BoundingBox(**bounding_box_dict)

        fcf.crop_and_segment_character(
            ad_id="test",
            bounding_box=bounding_box,
            logger=logger,
            base_path=mcw.GARLIC_TEST_PATH,
        )
