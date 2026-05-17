import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json as _json

ws_router = APIRouter()
active_connections: dict[int, list[WebSocket]] = {}
_loop: asyncio.AbstractEventLoop | None = None


def _get_loop():
    global _loop
    if _loop is None or _loop.is_closed():
        try:
            _loop = asyncio.get_running_loop()
        except RuntimeError:
            _loop = asyncio.new_event_loop()
    return _loop


async def broadcast(task_id: int, message: dict):
    for ws in active_connections.get(task_id, []):
        try:
            await ws.send_text(_json.dumps(message, default=str))
        except Exception:
            pass


def broadcast_sync(task_id: int, message: dict):
    """Thread-safe synchronous wrapper for broadcast."""
    loop = _get_loop()
    if loop.is_running():
        asyncio.run_coroutine_threadsafe(broadcast(task_id, message), loop)
    else:
        loop.run_until_complete(broadcast(task_id, message))


@ws_router.websocket("/ws/tasks/{task_id}")
async def task_trace(ws: WebSocket, task_id: int):
    await ws.accept()
    active_connections.setdefault(task_id, []).append(ws)
    try:
        # Keep connection alive until client disconnects
        while True:
            await ws.receive_text()
    except (WebSocketDisconnect, RuntimeError):
        pass
    finally:
        conns = active_connections.get(task_id, [])
        if ws in conns:
            conns.remove(ws)
        if not conns:
            active_connections.pop(task_id, None)
