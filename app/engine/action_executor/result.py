from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from app.engine.element_resolver import Match


class ActionExecutionError(Exception):
    def __init__(self, result: "ActionResult"):
        self.result = result
        super().__init__(repr(result))


@dataclass
class ActionResult:
    status: str
    action: str
    description: str

    selected_element: Optional[Match] = None
    score: Optional[float] = None
    value: Optional[Any] = None
    candidates: Optional[list[Match]] = None
    error: Optional[str] = None

    def __bool__(self) -> bool:
        return self.status == "success"

    def raise_if_error(self) -> "ActionResult":
        if self.status != "success":
            raise ActionExecutionError(self)

        return self

    def __repr__(self) -> str:
        # resto igual
        ...
        if self.status == "success":
            element = self.selected_element

            label = (
                element.label or element.text
                if element
                else ""
            )

            return (
                f"ActionResult("
                f"status='success', "
                f"action='{self.action}', "
                f"score={self.score:.2f}, "
                f"element='{label}'"
                f")"
            )

        if self.status == "ambiguous":
            scores = ", ".join(
                f"{candidate.score:.2f}"
                for candidate in (self.candidates or [])[:3]
            )

            return (
                f"ActionResult("
                f"status='ambiguous', "
                f"action='{self.action}', "
                f"candidates=[{scores}]"
                f")"
            )

        if self.status == "error":
            return (
                f"ActionResult("
                f"status='error', "
                f"action='{self.action}', "
                f"error='{self.error}'"
                f")"
            )

        return (
            f"ActionResult("
            f"status='not_found', "
            f"action='{self.action}', "
            f"description='{self.description}'"
            f")"
        )