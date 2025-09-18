"""Data models for the televised football calendar."""

from dataclasses import dataclass, field
from typing import Optional

import arrow


@dataclass
class Fixture:
    """Represents a single football fixture with broadcast information."""

    fixture: str
    kick_off: arrow.Arrow
    channel: str
    competition: str

    def __str__(self) -> str:
        return f"{self.fixture} ({self.competition}) at {self.kick_off.format('YYYY-MM-DD HH:mm')} on {self.channel}"


@dataclass
class Competition:
    """Represents a football competition with its data source and filtering options."""

    name: str
    url: str
    start_date: Optional[str] = None
    team_filters: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        return f"{self.name}: {self.url}"
