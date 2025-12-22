from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class OperationResult:
    ok: bool
    message: str | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def __bool__(self) -> bool:  # pragma: no cover - convenience
        return self.ok

    @classmethod
    def success(cls, message: str | None = None, **details: Any) -> OperationResult:
        return cls(True, message, dict(details))

    @classmethod
    def failure(cls, message: str | None = None, **details: Any) -> OperationResult:
        return cls(False, message, dict(details))


__all__ = ["OperationResult"]
