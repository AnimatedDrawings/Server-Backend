from pydantic import WebsocketUrl
import pytest
from fastapi import WebSocket, WebSocketDisconnect, FastAPI
from fastapi.testclient import TestClient


app = FastAPI()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_json()
            print(data)
            if data.get("type") != "ping":
                raise WebSocketDisconnect()
            await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        print("WebSocketDisconnect")
        await websocket.close()


@pytest.mark.asyncio
async def test_websocket_send():
    client = TestClient(app)

    with client.websocket_connect("/ws") as websocket:
        websocket.send_json({"gesg": "ping"})
        # for _ in range(10):
        #     # websocket.send_json({"type": "ping"})

        #     data = websocket.receive_json()
        #     assert data == {"type": "pong"}
