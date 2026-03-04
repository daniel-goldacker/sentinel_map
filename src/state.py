from __future__ import annotations

import asyncio
from collections import Counter, deque
from datetime import datetime, timezone
from typing import Any

from config import Settings


class RuntimeState:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.clients: set[Any] = set()
        self.lock = asyncio.Lock()

        self.total_events = 0
        self.recent_events: deque[dict[str, Any]] = deque(maxlen=settings.recent_events_limit)
        self.event_times: deque[float] = deque()

        self.country_counter: Counter[str] = Counter()
        self.path_counter: Counter[str] = Counter()
        self.type_counter: Counter[str] = Counter()

    def _prune_event_times(self, now_ts: float) -> None:
        threshold = now_ts - 60.0
        while self.event_times and self.event_times[0] < threshold:
            self.event_times.popleft()

    def events_per_minute(self) -> int:
        now_ts = datetime.now(timezone.utc).timestamp()
        self._prune_event_times(now_ts)
        return len(self.event_times)

    def stats_payload(self) -> dict[str, Any]:
        return {
            "total_events": self.total_events,
            "events_per_minute": self.events_per_minute(),
            "top_countries": dict(self.country_counter.most_common(8)),
            "top_paths": dict(self.path_counter.most_common(8)),
            "top_types": dict(self.type_counter.most_common(8)),
        }

    def snapshot(self) -> dict[str, Any]:
        return {
            "kind": "snapshot",
            "target": {
                "name": self.settings.target_name,
                "lat": self.settings.target_lat,
                "lon": self.settings.target_lon,
            },
            "stats": self.stats_payload(),
            "recent_events": list(self.recent_events),
        }
