from __future__ import annotations

import asyncio
import ipaddress
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from config import settings
from geoip_service import GeoIPService
from schemas import EventInput
from state import RuntimeState

state = RuntimeState(settings)
geoip = GeoIPService(str(settings.geoip_db_path))


@asynccontextmanager
async def lifespan(_: FastAPI):
    geoip.start()
    try:
        yield
    finally:
        geoip.stop()


app = FastAPI(title="Defensive Attack Map", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=settings.base_dir / "static"), name="static")


def get_client_ip(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "0.0.0.0"


def normalize_ip(raw_ip: str) -> str | None:
    try:
        return str(ipaddress.ip_address(raw_ip.strip()))
    except ValueError:
        return None


async def broadcast(payload: dict[str, Any]) -> None:
    dead: list[WebSocket] = []
    for ws in list(state.clients):
        try:
            await ws.send_json(payload)
        except Exception:
            dead.append(ws)

    for ws in dead:
        state.clients.discard(ws)


@app.get("/")
async def home() -> FileResponse:
    return FileResponse(settings.dashboard_path)


@app.get("/health")
async def health() -> dict[str, Any]:
    return {
        "ok": True,
        "geoip_loaded": geoip.is_loaded,
        "connected_clients": len(state.clients),
        "target": {
            "name": settings.target_name,
            "lat": settings.target_lat,
            "lon": settings.target_lon,
        },
    }


@app.get("/stats")
async def stats() -> dict[str, Any]:
    return state.stats_payload()


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket) -> None:
    await ws.accept()
    state.clients.add(ws)

    await ws.send_json(state.snapshot())

    try:
        while True:
            await asyncio.sleep(30)
            await ws.send_json({"kind": "heartbeat", "ts": datetime.now(timezone.utc).isoformat()})
    except WebSocketDisconnect:
        state.clients.discard(ws)


@app.post("/event")
async def ingest_event(request: Request, event: EventInput | None = None) -> dict[str, Any]:
    payload_in = event or EventInput()

    raw_ip = get_client_ip(request) or payload_in.ip
    ip = normalize_ip(raw_ip)
    if ip is None:
        return {"ok": False, "error": "invalid_ip", "received": raw_ip}

    path = payload_in.path or request.url.path
    ua = payload_in.ua or request.headers.get("user-agent", "")
    geo = geoip.lookup(ip)

    event_payload = {
        "kind": "event",
        "ts": datetime.now(timezone.utc).isoformat(),
        "ip": ip,
        "type": payload_in.type,
        "path": path,
        "ua": ua,
        "geo": geo,
        "target": {
            "name": settings.target_name,
            "lat": settings.target_lat,
            "lon": settings.target_lon,
        },
    }

    async with state.lock:
        state.total_events += 1

        now_ts = datetime.now(timezone.utc).timestamp()
        state.event_times.append(now_ts)
        state._prune_event_times(now_ts)

        country_key = (geo or {}).get("country") or "Unknown"
        state.country_counter[country_key] += 1
        state.path_counter[path] += 1
        state.type_counter[payload_in.type] += 1
        state.recent_events.appendleft(event_payload)

        stats_payload = {"kind": "stats", "stats": state.stats_payload()}

    await broadcast(event_payload)
    await broadcast(stats_payload)

    return {"ok": True, "broadcast": True, "event": event_payload}
