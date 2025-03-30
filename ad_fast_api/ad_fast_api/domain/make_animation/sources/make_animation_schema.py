from enum import Enum
from typing import TypedDict, Optional, Any


class ADAnimation(str, Enum):
    dab = "dab"
    zombie = "zombie"


class WebSocketType(str, Enum):
    ERROR = "ERROR"
    RUNNING = "RUNNING"
    FULL_JOB = "FULL_JOB"
    COMPLETE = "COMPLETE"


class WebSocketMessage(TypedDict):
    type: WebSocketType
    message: Optional[str]
    data: Optional[dict[str, Any]]


def create_websocket_message(
    type: WebSocketType,
    message: Optional[str] = None,
    data: Optional[dict[str, Any]] = None,
) -> WebSocketMessage:
    """웹소켓 메시지를 표준 형식으로 생성합니다."""
    return {
        "type": type,
        "message": message or "",
        "data": data or {},
    }
