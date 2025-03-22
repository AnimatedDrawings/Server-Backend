from locust import HttpUser, task
import gevent
from ad_fast_api.domain.upload_drawing.tests.case import (
    case_upload_drawing_router as cudr,
)
from ad_fast_api.workspace.sources import reqeust_files as rf
from ad_fast_api.snippets.sources.ad_case_test_helper import (
    remove_workspace,
)


class UploadDrawingUser(HttpUser):
    def on_start(self):
        # locust 유저가 시작될 때 샘플 이미지를 한 번 읽어 메모리에 저장합니다.
        upload_image = cudr.get_sample1_upload_image()
        self.files = {
            "file": (
                rf.UPLOAD_IMAGE_FILE_NAME,
                upload_image,
                "image/png",
            )
        }

    @task
    def upload_drawing(self):
        response = self.client.post(
            "/upload_drawing",
            files=self.files,
        )
        ad_id = response.json()["ad_id"]
        remove_workspace(ad_id=ad_id)
        gevent.sleep(5)


# sudo $(poetry run which python) locust_upload_drawing.py
# sudo $(which locust) -f locust_upload_drawing.py --host http://localhost:2010
# locust -f locust_upload_drawing.py --host http://localhost:2010
