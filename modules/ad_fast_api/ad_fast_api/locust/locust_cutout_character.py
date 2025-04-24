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
import logging
import psutil
import time
import threading
from locust import events


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


class CutoutCharacterUser(HttpUser):
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

        logging.warning(f"상태 코드: {response.status_code}")
        completed_time = time.time() - start_test_time  # type: ignore
        logging.warning(f"완료 시간: {completed_time}초")
        if response.status_code >= 400:
            try:
                error_detail = response.json().get("detail", "상세 오류 정보 없음")
                logging.error(f"HTTP 예외 상세 정보: {error_detail}")
            except Exception as e:
                logging.error(f"응답 JSON 파싱 실패: {e}")

        remove_workspace(ad_id=ad_id)
        gevent.sleep(5)


# sudo $(poetry run which python) locust_cutout_character.py
# sudo $(which locust) -f locust_cutout_character.py --loglevel=WARNING
# locust -f locust_cutout_character.py
