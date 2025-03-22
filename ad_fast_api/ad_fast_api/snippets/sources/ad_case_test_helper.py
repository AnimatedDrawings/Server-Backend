from ad_fast_api.workspace.sources import conf_workspace as cw
from uuid import uuid4
import shutil


def remove_workspace(ad_id: str):
    tmp_base_path = cw.get_base_path(ad_id=ad_id)
    shutil.rmtree(tmp_base_path)


def init_workspace(example_name: str) -> str:
    src_folder = cw.get_base_path(ad_id=example_name)

    ad_id = str(uuid4())
    dst_folder = cw.get_base_path(ad_id=ad_id)
    shutil.copytree(src_folder, dst_folder)

    return ad_id
