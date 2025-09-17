"""Data models for the televised football calendar."""

from dataclasses import dataclass

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
    """Represents a football competition with its data source."""

    name: str
    url: str

    def __str__(self) -> str:
        return f"{self.name}: {self.url}"
