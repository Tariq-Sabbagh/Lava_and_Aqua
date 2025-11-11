from dataclasses import dataclass
from typing import Any, Literal

Status = Literal["ok", "blocked", "win", "lose"]


@dataclass(frozen=True)
class Result:
    ok: bool
    status: Status
    reason: str | None = None
    data: dict[str, Any] | None = None
