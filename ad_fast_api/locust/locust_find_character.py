from locust import HttpUser, task
import gevent
from pathlib import Path
import yaml
import shutil

from ad_fast_api.domain.upload_drawing.sources.features.configure_work_dir import (
    make_ad_id,
)


def copy_result_garlic(dir_name: str):
    cur_dir = Path(__file__).parent

    garlic_dir = cur_dir.parent / "workspace" / "files" / dir_name
    garlic_dir.mkdir(parents=True, exist_ok=True)

    shutil.copytree(
        cur_dir / "result_garlic",
        garlic_dir,
        ignore=shutil.ignore_patterns("*.gif"),
        dirs_exist_ok=True,
    )


class FindCharacterUser(HttpUser):
    def get_params(self, ad_id: str):
        return {"ad_id": ad_id}

    def on_start(self):
        bounding_box_path = (
            Path(__file__).parent / "result_garlic" / "bounding_box.yaml"
        )
        with open(bounding_box_path, "r") as f:
            self.bounding_box = yaml.safe_load(f)

    @task
    def find_character(self):
        ad_id = make_ad_id()
        copy_result_garlic(ad_id)

        gevent.sleep(5)

        self.client.post(
            "/find_character",
            json=self.bounding_box,
            params=self.get_params(ad_id),
        )


# locust -f locust_find_character.py --host http://localhost:2010

if __name__ == "__main__":
    copy_result_garlic("result_garlic111")
