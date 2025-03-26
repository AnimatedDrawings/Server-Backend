from locust import HttpUser, task, between
import gevent
import websocket
import json
import time
from ad_fast_api.workspace.sources import reqeust_files as rf
from ad_fast_api.snippets.sources.ad_case_test_helper import (
    init_workspace,
    remove_workspace,
)


class MakeAnimationUser(HttpUser):
    wait_time = between(2, 4)
    host = "http://localhost:2010"

    def on_start(self):
        self.ad_animation = "dab"

    @task(1)
    def test_websocket_endpoint(self):
        example_name = rf.EXAMPLE1_AD_ID
        ad_id = init_workspace(example_name=example_name)
        ws_host = self.host.replace(
            "http://", "ws://"
        )  # HTTP 호스트를 WS 호스트로 변환
        ws_url = (
            f"{ws_host}/make_animation?ad_id={ad_id}&ad_animation={self.ad_animation}"
        )

        start_time = time.time()

        def on_open(ws):
            connect_time = time.time() - start_time
            self.environment.events.request.fire(
                request_type="WebSocket",
                name="connect",
                response_time=connect_time * 1000,
                response_length=0,
                response=None,
                context={},
                exception=None,
            )

        def on_message(ws, message):
            data = json.loads(message)
            if data.get("type") == "ERROR":
                self.environment.events.request.fire(
                    request_type="WebSocket",
                    name="message",
                    response_time=0,
                    response_length=len(message),
                    response=None,
                    context={},
                    exception=data.get("message", "Unknown error"),
                )
                ws.close()
            elif data.get("type") == "ping":
                # ping 메시지를 받으면 pong으로 응답
                self.environment.events.request.fire(
                    request_type="WebSocket",
                    name="ping_received",
                    response_time=0,
                    response_length=len(message),
                    response=None,
                    context={},
                    exception=None,
                )
                ws.send(json.dumps({"type": "pong", "message": "", "data": {}}))
            elif data.get("type") == "COMPLETE":
                complete_time = (time.time() - start_time) * 1000
                self.environment.events.request.fire(
                    request_type="WebSocket",
                    name="message",
                    response_time=complete_time,
                    response_length=len(message),
                    response=None,
                    context={},
                    exception=None,
                )
                ws.close()
            else:
                self.environment.events.request.fire(
                    request_type="WebSocket",
                    name=f"message_{data.get('type', 'unknown')}",
                    response_time=0,
                    response_length=len(message),
                    response=None,
                    context={},
                    exception=None,
                )

        def on_ping(ws, message):
            # 서버로부터 ping 메시지 수신 시 pong 응답을 전송합니다
            self.environment.events.request.fire(
                request_type="WebSocket",
                name="ping_received",
                response_time=0,
                response_length=len(message) if message else 0,
                response=None,
                context={},
                exception=None,
            )
            ws.send(json.dumps({"type": "pong", "message": "", "data": {}}))

        def on_error(ws, error):
            self.environment.events.request.fire(
                request_type="WebSocket",
                name="connection",
                response_time=(time.time() - start_time) * 1000,
                response_length=0,
                response=None,
                context={},
                exception=str(error),
            )

        ws_app = websocket.WebSocketApp(
            ws_url,
            on_open=on_open,
            on_message=on_message,
            on_ping=on_ping,
            on_error=on_error,
            on_close=lambda ws, close_status_code, close_msg: None,
        )

        # ping_interval 값은 유지하고 ping_timeout을 조금 더 길게 설정
        ws_app.run_forever(ping_interval=10, ping_timeout=8, ping_payload="ping")

        remove_workspace(ad_id=ad_id)
        gevent.sleep(3)


# sudo $(poetry run which python) locust_make_animation.py
# sudo $(which locust) --processes 3 -f locust_make_animation.py
# locust -f locust_make_animation.py
