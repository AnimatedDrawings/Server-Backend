from locust import HttpUser, task, between
import gevent
from ad_fast_api.domain.cutout_character.tests.case import (
    case_cutout_character_router as cccr,
)
from ad_fast_api.workspace.sources import reqeust_files as rf
from ad_fast_api.snippets.sources.ad_case_test_helper import (
    init_workspace,
    remove_workspace,
)


class CutoutCharacterUser(HttpUser):
    wait_time = between(2, 4)
    host = "http://localhost:2010"

    def on_start(self):
        cutout_character_image = cccr.get_sample1_cutout_character_image()
        self.files = {
            "file": (
                rf.CUTOUT_CHARACTER_IMAGE_FILE_NAME,
                cutout_character_image,
                "image/png",
            )
        }

    def make_params(self, ad_id: str):
        return {"ad_id": ad_id}

    @task
    def cutout_character(self):
        example_name = rf.EXAMPLE1_AD_ID
        ad_id = init_workspace(example_name=example_name)
        params = self.make_params(ad_id=ad_id)

        response = self.client.post(
            "/cutout_character",
            params=params,
            files=self.files,
        )

        remove_workspace(ad_id=ad_id)
        gevent.sleep(3)


# sudo $(poetry run which python) locust_cutout_character.py
# sudo $(which locust) -f locust_cutout_character.py
# locust -f locust_cutout_character.py
