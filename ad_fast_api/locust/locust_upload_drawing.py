from locust import HttpUser, task
import gevent
from ad_fast_api.workspace.testings.request_files import mock_conf_workspace as mcw


def get_sample1_upload_image():
    base_path = mcw.EXAMPLE1_BASE_PATH
    sample_image_path = base_path / mcw.UPLOAD_IMAGE_FILE_NAME

    if not sample_image_path.exists():
        raise FileNotFoundError(
            f"locust_upload_drawing.py, upload image file not found: {sample_image_path}"
        )

    with open(sample_image_path, "rb") as f:
        return f.read()


class UploadDrawingUser(HttpUser):
    def on_start(self):
        self.sample_image = get_sample1_upload_image()
        # locust 유저가 시작될 때 샘플 이미지를 한 번 읽어 메모리에 저장합니다.

    @task
    def upload_drawing(self):
        files = {"file": ("upload_image.png", self.sample_image, "image/png")}
        self.client.post("/upload_drawing", files=files)
        gevent.sleep(5)


# locust -f locust_upload_drawing.py --host http://localhost:2010


if __name__ == "__main__":
    image = get_sample1_upload_image()
    print(image)
