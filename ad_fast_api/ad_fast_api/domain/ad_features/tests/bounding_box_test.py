from ad_fast_api.domain.schema.sources.schemas import BoundingBox
from ad_fast_api.domain.ad_features.sources.bounding_box_feature import (
    save_bounding_box,
)
from ad_fast_api.workspace.sources import conf_workspace as cw
from pathlib import Path
from ad_fast_api.snippets.sources.ad_test import measure_execution_time
import yaml


def test_save_bounding_box_success(tmp_path: Path):
    # given
    bounding_box = BoundingBox.mock()
    base_path = tmp_path
    bounding_box_file_name = cw.BOUNDING_BOX_FILE_NAME
    expected_path = base_path.joinpath(bounding_box_file_name)
    bounding_box_dict = bounding_box.model_dump(mode="json")
    bounding_box_yaml = yaml.dump(bounding_box_dict)

    # when
    measure_execution_time("save_bounding_box")(save_bounding_box)(
        bounding_box=bounding_box,
        base_path=base_path,
    )

    # then
    assert expected_path.exists()
    assert expected_path.read_text() == bounding_box_yaml
