from locust import HttpUser, task, between
import gevent


class PingUser(HttpUser):
    wait_time = between(1, 2)  # 기본 태스크 간의 대기 시간

    @task
    def ping(self):
        self.client.get("/ping")
        # 태스크 내 추가적인 지연: 예를 들어 2초 대기
        gevent.sleep(7)


# locust -f locust_ping.py --host http://localhost:2010
