"""Boundary for a future implementation of the verified paper model."""

from dataclasses import dataclass
from datetime import datetime
from json import loads
from typing import Literal, Protocol

from .inputs import Series

SECTIONS = ("hydrogen_conversion", "cost_budget", "dispatch_equations")


def _reject_constant(value: str) -> None:
    raise ValueError(f"Invalid JSON numeric constant: {value}")


@dataclass(frozen=True)
class ModelParameters:
    hydrogen_conversion: dict | None
    cost_budget: dict | None
    dispatch_equations: dict | None

    @classmethod
    def from_json(cls, data: bytes) -> "ModelParameters":
        values = loads(data, parse_constant=_reject_constant)
        if not isinstance(values, dict) or set(values) != set(SECTIONS):
            raise ValueError("Model JSON must contain exactly: " + ", ".join(SECTIONS))
        for name, value in values.items():
            if value is not None and not isinstance(value, dict):
                raise ValueError(f"{name} must be an object or null")
        return cls(**values)

    @property
    def unresolved(self) -> tuple[str, ...]:
        return tuple(name for name in SECTIONS if not getattr(self, name))


@dataclass(frozen=True)
class DispatchResult:
    status: Literal["optimal", "feasible", "infeasible", "unbounded", "error"]
    solver_name: str
    solver_version: str
    timestamps: tuple[datetime, ...] = ()
    grid_import_kw: tuple[float, ...] = ()


class DispatchSolver(Protocol):
    """Adapters validate their model parameters and align results with input timestamps."""

    def solve(self, series: Series, parameters: ModelParameters) -> DispatchResult:
        """Return termination status and a schedule when a feasible solution exists."""
        ...
