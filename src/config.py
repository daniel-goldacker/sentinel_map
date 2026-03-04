from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    base_dir: Path
    target_name: str = "Servidor Principal"
    target_lat: float = -23.5505
    target_lon: float = -46.6333
    recent_events_limit: int = 100

    @property
    def geoip_db_path(self) -> Path:
        return self.base_dir / "data" / "GeoLite2-City.mmdb"

    @property
    def dashboard_path(self) -> Path:
        return self.base_dir / "static" / "index.html"


settings = Settings(base_dir=Path(__file__).resolve().parents[1])
