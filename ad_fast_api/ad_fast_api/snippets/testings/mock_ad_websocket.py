from fastapi.websockets import WebSocket
from logging import Logger


class DummyWebSocket(WebSocket):
    def __init__(self, responses, send_json_side_effect=None, accept_exception=None):
        self.responses = responses[:]  # 복사본 사용
        self.send_json_side_effect = send_json_side_effect
        self.accept_exception = accept_exception
        self.closed = False
        self.last_sent = None

    async def receive_json(self):
        if self.responses:
            return self.responses.pop(0)
        return {}

    async def send_json(self, data):
        if self.send_json_side_effect:
            raise self.send_json_side_effect
        self.last_sent = data

    async def accept(self):
        if self.accept_exception:
            raise self.accept_exception

    async def close(self, code, reason):
        self.closed = True
        self.close_code = code
        self.close_reason = reason


class DummyLogger(Logger):
    def __init__(self):
        self.logs = []

    def info(self, msg, *args):
        self.logs.append(("info", msg % args if args else msg))

    def error(self, msg, *args):
        self.logs.append(("error", msg % args if args else msg))

    def exception(self, msg, *args):
        self.logs.append(("exception", msg % args if args else msg))
