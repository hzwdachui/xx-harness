from fastapi import APIRouter, WebSocket, WebSocketDisconnect

ws_router = APIRouter()
active_connections: dict[int, list[WebSocket]] = {}

@ws_router.websocket("/ws/tasks/{task_id}")
async def task_trace(ws: WebSocket, task_id: int):
    await ws.accept()
    active_connections.setdefault(task_id, []).append(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        active_connections[task_id].remove(ws)
