from locust import HttpUser, task
import gevent
from ad_fast_api.domain.make_animation.tests.case import (
    case_make_animation_router as cmar,
)
from ad_fast_api.workspace.sources import reqeust_files as rf


class MakeAnimationUser(HttpUser):
    def on_start(self):
        # locust 유저가 시작될 때 샘플 이미지를 한 번 읽어 메모리에 저장합니다.
        ad_id = rf.EXAMPLE1_AD_ID
        self.ad_id = ad_id
        ad_animation = "dab"
        self.params = {
            "ad_id": ad_id,
            "ad_animation": ad_animation,
        }

    @task
    def make_animation(self):
        response = self.client.post(
            "/make_animation",
            params=self.params,
        )
        cmar.remove_result_video_files(ad_id=self.ad_id)
        gevent.sleep(5)


# sudo $(poetry run which python) locust_make_animation.py
# sudo $(which locust) -f locust_make_animation.py --host http://localhost:2010
# locust -f locust_make_animation.py --host http://localhost:2010
