from locust import HttpUser, task
import gevent
from ad_fast_api.domain.upload_drawing.tests.case import (
    case_upload_drawing_router as cudr,
)


class UploadDrawingUser(HttpUser):
    def on_start(self):
        # locust 유저가 시작될 때 샘플 이미지를 한 번 읽어 메모리에 저장합니다.
        self.sample_image = cudr.get_sample1_upload_image()

    @task
    def upload_drawing(self):
        files = {"file": ("upload_image.png", self.sample_image, "image/png")}
        response = self.client.post("/upload_drawing", files=files)
        ad_id = response.json()["ad_id"]
        cudr.remove_workspace_files(ad_id=ad_id)
        gevent.sleep(5)


# sudo $(poetry run which python) locust_upload_drawing.py
# sudo $(which locust) -f locust_upload_drawing.py --host http://localhost:2010
# locust -f locust_upload_drawing.py --host http://localhost:2010
