import websocket
from ad_fast_api.domain.make_animation.sources.make_animation_schema import (
    WebSocketType,
)
import time
import json


class WebSocketClient:
    def __init__(self, connection_id, url, environment, teardown):
        self.connection_id = connection_id
        self.url = url
        self.environment = environment
        self.ws = None
        self.start_time = time.time()
        self.teardown = teardown

    def connect(self):
        self.ws = websocket.WebSocketApp(
            self.url,
            on_open=self.on_open,
            on_message=self.on_message,
            on_close=self.on_close,
        )

        self.ws.run_forever()

    def log_event(
        self,
        name,
        response_time=None,
        response_length=None,
        response=None,
        context=None,
        exception=None,
    ):
        tmp_context = {"connection_id": self.connection_id}
        if context:
            tmp_context.update(context)

        self.environment.events.request.fire(
            request_type="WebSocket",
            name=name,
            response_time=response_time or 0,
            response_length=response_length or 0,
            response=response or None,
            context=tmp_context,
            exception=exception or None,
        )

    def on_open(self, ws):
        connect_time = time.time() - self.start_time
        self.log_event(
            name=f"on_open",
            response_time=connect_time * 1000,
        )

    def on_close(self, ws, close_status_code, close_msg):
        self.log_event(
            name=f"on_close",
            context={
                "status_code": close_status_code,
                "message": close_msg,
                "connection_duration": time.time() - self.start_time,
            },
        )
        # 연결 종료 시 teardown 호출
        # self.teardown()

    def on_message(self, ws, message):
        try:
            data = json.loads(message)
            data_type = data.get("type")
        except json.JSONDecodeError:
            self.log_event(
                name="on_message, invalid_json",
                response_length=len(message),
            )
            ws.close()
            return

        if data_type == "ping":
            self.log_event(
                name=f"ping pong",
                response_length=len(message),
            )
            ws.send(
                json.dumps(
                    {
                        "type": "pong",
                        "message": "",
                        "data": {},
                    },
                )
            )

        elif data_type == WebSocketType.ERROR:
            msg = data.get("message", "Unknown error")
            self.log_event(
                name=f"{data_type}, {self.connection_id}",
                response_length=len(message),
                response=msg,
            )
            ws.close()

        elif data_type == WebSocketType.RUNNING:
            self.log_event(
                name=f"{data_type}, {self.connection_id}",
                response_length=len(message),
            )

        elif data_type == WebSocketType.FULL_JOB:
            msg = data.get("message", "Unknown full job")
            self.log_event(
                name=f"{data_type}",
                response_length=len(message),
                response=msg,
            )
            self.teardown()
            ws.close()

        elif data_type == WebSocketType.COMPLETE:
            complete_time = (time.time() - self.start_time) * 1000
            self.log_event(
                name=f"{data_type}, {self.connection_id}",
                response_time=complete_time,
            )
            self.teardown()
            ws.close()

        else:
            msg = f"Unknown message: {data_type or 'unknown'}"
            self.log_event(
                name=f"unknown_message, {self.connection_id}",
                response_length=len(message),
                response=msg,
            )
            ws.close()
