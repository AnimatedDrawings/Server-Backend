import yaml
from ad_fast_api.domain.schema.sources.schemas import BoundingBox
from ad_fast_api.workspace.sources import conf_workspace as cw
from pathlib import Path


def save_bounding_box(
    bounding_box: BoundingBox,
    base_path: Path,
):
    bounding_box_path = base_path.joinpath(cw.BOUNDING_BOX_FILE_NAME)
    bounding_box_dict = bounding_box.model_dump(mode="json")
    content = yaml.dump(bounding_box_dict)
    with open(bounding_box_path.as_posix(), "w") as f:
        f.write(content)
