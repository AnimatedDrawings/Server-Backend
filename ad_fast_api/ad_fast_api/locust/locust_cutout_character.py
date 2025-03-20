from locust import HttpUser, task
import gevent
from ad_fast_api.domain.cutout_character.tests.case import (
    case_cutout_character_router as cccr,
)
from ad_fast_api.workspace.sources import reqeust_files as rf


class CutoutCharacterUser(HttpUser):
    def on_start(self):
        # locust 유저가 시작될 때 샘플 이미지를 한 번 읽어 메모리에 저장합니다.
        ad_id = rf.EXAMPLE1_AD_ID
        self.params = {"ad_id": ad_id}

        cutout_character_image = cccr.get_sample1_cutout_character_image()
        self.files = {
            "file": (
                rf.CUTOUT_CHARACTER_IMAGE_FILE_NAME,
                cutout_character_image,
                "image/png",
            )
        }

    @task
    def cutout_character(self):
        response = self.client.post(
            "/cutout_character",
            params=self.params,
            files=self.files,
        )
        print(response.json())
        gevent.sleep(5)


# sudo $(poetry run which python) locust_cutout_character.py
# sudo $(which locust) -f locust_cutout_character.py --host http://localhost:2010
#


"""
[2025-03-20 11:09:15,877] chmini-server/ERROR/locust.user.task: Expecting value: line 1 column 1 (char 0)
Traceback (most recent call last):
  File "/opt/stacks/ad-server-dev/ad_fast_api/.venv/lib/python3.13/site-packages/requests/models.py", line 974, in json
    return complexjson.loads(self.text, **kwargs)
           ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
  File "/home/chmini/.pyenv/versions/3.13.2/lib/python3.13/json/__init__.py", line 346, in loads
    return _default_decoder.decode(s)
           ~~~~~~~~~~~~~~~~~~~~~~~^^^
  File "/home/chmini/.pyenv/versions/3.13.2/lib/python3.13/json/decoder.py", line 345, in decode
    obj, end = self.raw_decode(s, idx=_w(s, 0).end())
               ~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/chmini/.pyenv/versions/3.13.2/lib/python3.13/json/decoder.py", line 363, in raw_decode
    raise JSONDecodeError("Expecting value", s, err.value) from None
json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/opt/stacks/ad-server-dev/ad_fast_api/.venv/lib/python3.13/site-packages/locust/user/task.py", line 340, in run
    self.execute_next_task()
    ~~~~~~~~~~~~~~~~~~~~~~^^
  File "/opt/stacks/ad-server-dev/ad_fast_api/.venv/lib/python3.13/site-packages/locust/user/task.py", line 373, in execute_next_task
    self.execute_task(self._task_queue.popleft())
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/stacks/ad-server-dev/ad_fast_api/.venv/lib/python3.13/site-packages/locust/user/task.py", line 490, in execute_task
    task(self.user)
    ~~~~^^^^^^^^^^^
  File "/opt/stacks/ad-server-dev/ad_fast_api/ad_fast_api/locust/locust_cutout_character.py", line 31, in cutout_character
    print(response.json())
          ~~~~~~~~~~~~~^^
  File "/opt/stacks/ad-server-dev/ad_fast_api/.venv/lib/python3.13/site-packages/requests/models.py", line 978, in json
    raise RequestsJSONDecodeError(e.msg, e.doc, e.pos)
requests.exceptions.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
"""
