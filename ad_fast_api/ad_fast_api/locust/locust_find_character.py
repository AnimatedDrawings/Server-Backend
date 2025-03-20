from locust import HttpUser, task
import gevent
from ad_fast_api.workspace.sources import reqeust_files as rf
from ad_fast_api.domain.find_character.tests.case import (
    case_find_character_router as cfcr,
)


class FindCharacterUser(HttpUser):
    def on_start(self):
        ad_id = rf.EXAMPLE1_AD_ID
        self.params = {"ad_id": ad_id}

        bounding_box_dict = cfcr.get_sample1_bounding_box_dict()
        self.json = bounding_box_dict

    @task
    def find_character(self):
        response = self.client.post(
            "/find_character",
            params=self.params,
            json=self.json,
        )

        gevent.sleep(5)


# # locust -f locust_find_character.py --host http://localhost:2010
