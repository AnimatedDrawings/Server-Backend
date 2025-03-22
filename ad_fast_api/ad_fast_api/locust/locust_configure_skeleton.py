from locust import HttpUser, task, between
import gevent
from ad_fast_api.workspace.sources import conf_workspace as cw
from ad_fast_api.workspace.sources import reqeust_files as rf
from ad_fast_api.snippets.sources.ad_logger import setup_logger
from ad_fast_api.domain.cutout_character.sources.features.configure_skeleton import (
    get_cropped_image,
)
import cv2
import json


class ConfigureSkeletonUser(HttpUser):
    wait_time = between(2, 4)
    host = "http://localhost:8080"

    def on_start(self):
        ad_id = rf.EXAMPLE1_AD_ID
        base_path = cw.get_base_path(ad_id=ad_id)
        logger = setup_logger(base_path=base_path)
        cropped_image = get_cropped_image(
            base_path=base_path,
            logger=logger,
        )

        img_b = cv2.imencode(".png", cropped_image)[1].tobytes()
        files = {"data": img_b}

        self.logger = logger
        self.files = files

    def check_response(self, response):
        status_code = response.status_code
        if status_code != 200:
            print("---Error---")
            print(f"Error: Non-200 status code : {status_code}")
            # 오류 유형에 따른 세부 처리 추가
            if status_code == 503:
                print("Server is overloaded, backing off...")
                # gevent.sleep(5)  # 오버로드 시 더 오래 대기
            elif status_code == 408:
                print("Request timed out")
            print(f"Response Content: {response.content}")
            print()
        else:
            try:
                pose_results = json.loads(response.content)
                print("---Success---")
                print(pose_results)
                print()
            except Exception as decode_error:
                print("---Error---")
                print(f"Response Content: {response.content}")
                print(f"Decode Error: {decode_error}")
                print()

    @task
    def cutout_character(self):
        try:
            response = self.client.post(
                "/predictions/drawn_humanoid_pose_estimator",
                files=self.files,
                timeout=25,  # 클라이언트 타임아웃 설정
            )
            self.check_response(response)
        except Exception as e:
            print(f"Request failed: {str(e)}")

        # 요청 간 간격을 더 길게 설정하여 서버 과부하 방지
        gevent.sleep(3)


# locust -f locust_configure_skeleton.py
