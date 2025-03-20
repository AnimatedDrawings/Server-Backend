from locust import HttpUser, task
import gevent
from ad_fast_api.workspace.sources import reqeust_files as rf
from ad_fast_api.domain.configure_character_joints.tests.case import (
    case_configure_character_joints_router as cccjr,
)


class ConfigureCharacterJointsUser(HttpUser):
    def on_start(self):
        ad_id = rf.EXAMPLE1_AD_ID
        self.params = {"ad_id": ad_id}

        char_cfg_dict = cccjr.get_char_cfg_dict()
        self.json = char_cfg_dict

    @task
    def configure_character_joints(self):
        response = self.client.post(
            "/configure_character_joints",
            params=self.params,
            json=self.json,
        )

        gevent.sleep(1)


# locust -f locust_configure_character_joints.py --host http://localhost:2010
