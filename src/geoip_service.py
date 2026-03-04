from __future__ import annotations

from typing import Any

from geoip2.database import Reader


class GeoIPService:
    def __init__(self, database_path: str) -> None:
        self.database_path = database_path
        self.reader: Reader | None = None

    def start(self) -> None:
        try:
            self.reader = Reader(self.database_path)
        except Exception:
            self.reader = None

    def stop(self) -> None:
        if self.reader is not None:
            self.reader.close()
            self.reader = None

    @property
    def is_loaded(self) -> bool:
        return self.reader is not None

    def lookup(self, ip: str) -> dict[str, Any] | None:
        if self.reader is None:
            return None

        try:
            result = self.reader.city(ip)
            lat = result.location.latitude
            lon = result.location.longitude
            if lat is None or lon is None:
                return None

            return {
                "lat": lat,
                "lon": lon,
                "country": result.country.name or "Unknown",
                "city": result.city.name or "",
            }
        except Exception:
            return None
