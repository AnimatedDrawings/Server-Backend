from locust import HttpUser, task, between
import gevent
from ad_fast_api.workspace.sources import reqeust_files as rf
from ad_fast_api.snippets.sources.ad_case_test_helper import (
    init_workspace,
    remove_workspace,
)
from ad_fast_api.locust.ws_client import WebSocketClient


class MakeAnimationUser(HttpUser):
    wait_time = between(2, 4)
    host = "http://localhost:2010"

    def on_start(self):
        self.ad_animation = "dab"

    @task
    def test_websocket_endpoint(self):
        example_name = rf.EXAMPLE1_AD_ID
        ad_id = init_workspace(example_name=example_name)
        ws_host = self.host.replace(  # type: ignore
            "http://", "ws://"
        )  # HTTP 호스트를 WS 호스트로 변환
        ws_url = (
            f"{ws_host}/make_animation?ad_id={ad_id}&ad_animation={self.ad_animation}"
        )

        ws_client = WebSocketClient(
            connection_id=ad_id,
            url=ws_url,
            environment=self.environment,
            teardown=lambda: remove_workspace(ad_id),
        )
        ws_client.connect()

        gevent.sleep(3)


# sudo $(poetry run which python) locust_make_animation.py
# sudo $(which locust) --processes -1 -f locust_make_animation.py
# sudo $(which locust) --processes 10 -f locust_make_animation.py
# locust -f locust_make_animation.py
