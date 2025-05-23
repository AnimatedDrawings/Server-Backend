import logging
import time
import gevent
from locust import HttpUser, task, between, events
from ad_fast_api.workspace.sources import reqeust_files as rf
from ad_fast_api.snippets.sources.ad_case_test_helper import (
    init_workspace,
    remove_workspace,
)
from ad_fast_api.locust.locust_helper.ws_client import WebSocketClient
from ad_fast_api.locust.locust_helper.locust_record_time import record_time
import psutil
import threading


start_test_time = None
max_cpu_usage = 0


def monitor_cpu(interval=1):
    global max_cpu_usage
    while True:
        # interval 시간 동안의 CPU 사용률 측정
        usage = psutil.cpu_percent(interval=interval)
        if usage > max_cpu_usage:
            max_cpu_usage = usage


@events.test_start.add_listener
def on_start_load_test(environment, **kwargs):
    global start_test_time

    start_test_time = time.time()

    logging.warning(
        f"테스트 시작 시간: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_test_time))}"
    )

    cpu_monitor_thread = threading.Thread(target=monitor_cpu, args=(1,), daemon=True)
    cpu_monitor_thread.start()


@events.test_stop.add_listener
def on_stop_load_test(environment, **kwargs):
    stop_time = time.time()

    logging.warning(
        f"테스트 종료 시간: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stop_time))}"
    )
    logging.warning(f"최대 CPU 사용량: {max_cpu_usage}%")


class MakeAnimationUser(HttpUser):
    host = "http://localhost:2010"

    def on_start(self):
        self.ad_animation = "dab"

    @task
    def test_make_animation_websocket(self):
        example_name = rf.EXAMPLE1_AD_ID
        ad_id = init_workspace(example_name=example_name)
        ws_host = self.host.replace("http://", "ws://")  # type: ignore
        ws_url = (
            f"{ws_host}/make_animation?ad_id={ad_id}&ad_animation={self.ad_animation}"
        )

        ws_client = WebSocketClient(
            connection_id=ad_id,
            url=ws_url,
            environment=self.environment,
            # teardown=lambda: remove_workspace(ad_id),
            teardown=lambda: None,
            start_test_time=start_test_time,
        )
        ws_client.connect()

        gevent.sleep(5)


# sudo $(poetry run which python) locust_make_animation.py
# sudo $(which locust) --processes -1 -f locust_make_animation.py --loglevel=WARNING
# sudo $(which locust) --processes 10 -f locust_make_animation.py --loglevel=WARNING
# sudo $(which locust) --processes 3 -f locust_make_animation.py --loglevel=WARNING
# locust -f locust_make_animation.py
