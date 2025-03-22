from locust import HttpUser, task, between
import gevent
from ad_fast_api.workspace.sources import reqeust_files as rf
from ad_fast_api.snippets.sources.ad_case_test_helper import (
    init_workspace,
    remove_workspace,
)


class MakeAnimationUser(HttpUser):
    wait_time = between(2, 4)
    host = "http://localhost:2010"

    def on_start(self):
        pass

    def make_params(
        self,
        ad_id: str,
        ad_animation: str = "dab",
    ):
        return {
            "ad_id": ad_id,
            "ad_animation": ad_animation,
        }

    @task
    def make_animation(self):
        example_name = rf.EXAMPLE1_AD_ID
        ad_id = init_workspace(example_name=example_name)
        params = self.make_params(ad_id=ad_id)

        response = self.client.post(
            "/make_animation",
            params=params,
            timeout=90,
        )

        remove_workspace(ad_id=ad_id)
        gevent.sleep(3)


# sudo $(poetry run which python) locust_make_animation.py
# sudo $(which locust) -f locust_make_animation.py
# locust -f locust_make_animation.py
