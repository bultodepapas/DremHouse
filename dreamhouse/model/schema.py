"""Small dependency-free types shared by the integrated project pipeline."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal

CheckStatus = Literal["PASS", "OPEN", "FAIL"]


class ModelError(ValueError):
    """The canonical model is missing, stale, contradictory, or invalid."""


@dataclass(frozen=True)
class CheckResult:
    """One deterministic validation result with authority-safe status."""

    rule_id: str
    status: CheckStatus
    message: str
    entity_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def check(
    rule_id: str,
    passed: bool,
    message: str,
    *,
    entity_ids: tuple[str, ...] = (),
) -> CheckResult:
    """Create a binary PASS/FAIL result."""

    return CheckResult(
        rule_id=rule_id,
        status="PASS" if passed else "FAIL",
        message=message,
        entity_ids=entity_ids,
    )


def open_check(
    rule_id: str,
    message: str,
    *,
    entity_ids: tuple[str, ...] = (),
) -> CheckResult:
    """Create an explicit unresolved professional or owner gate."""

    return CheckResult(
        rule_id=rule_id,
        status="OPEN",
        message=message,
        entity_ids=entity_ids,
    )
