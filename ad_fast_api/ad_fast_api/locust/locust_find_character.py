from locust import HttpUser, task
import gevent
from ad_fast_api.workspace.sources import reqeust_files as rf
from ad_fast_api.workspace.sources import conf_workspace as cw
from ad_fast_api.domain.find_character.tests.case import (
    case_find_character_router as cfcr,
)
from ad_fast_api.snippets.sources.ad_case_test_helper import (
    init_workspace,
    remove_workspace,
)


class FindCharacterUser(HttpUser):
    def on_start(self):
        bounding_box_dict = cfcr.get_sample1_bounding_box_dict()
        self.json = bounding_box_dict

    def make_params(self, ad_id: str):
        return {"ad_id": ad_id}

    @task
    def find_character(self):
        example_name = rf.EXAMPLE1_AD_ID
        ad_id = init_workspace(example_name=example_name)
        params = self.make_params(ad_id=ad_id)

        response = self.client.post(
            "/find_character",
            params=params,
            json=self.json,
        )

        remove_workspace(ad_id=ad_id)
        gevent.sleep(3)


# # locust -f locust_find_character.py --host http://localhost:2010
