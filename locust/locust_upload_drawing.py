from locust import HttpUser, task
import gevent
from pathlib import Path


class UploadDrawingUser(HttpUser):
    def on_start(self):
        # locust 유저가 시작될 때 샘플 이미지를 한 번 읽어 메모리에 저장합니다.
        sample_image_path = Path(__file__).parent / "result_garlic" / "origin_image.png"
        with open(sample_image_path, "rb") as f:
            self.sample_image = f.read()

    @task
    def upload_drawing(self):
        files = {"file": ("sample_image.png", self.sample_image, "image/png")}
        self.client.post("/upload_drawing", files=files)
        gevent.sleep(5)


# locust -f locust_upload_drawing.py --host http://localhost:2010
