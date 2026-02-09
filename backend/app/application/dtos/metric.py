"""DTOs for the metrics engine context."""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True)
class CatalogEntryDTO:
    """A single metric definition from the catalog."""

    id: UUID
    name: str
    display_name: str
    description: str | None
    unit: str | None
    value_type: str


@dataclass(frozen=True)
class CustomerMetricDTO:
    """A customer's current value for a specific metric, enriched with definition info."""

    metric_definition_id: UUID
    metric_name: str
    display_name: str
    metric_value: Decimal
    unit: str | None
    description: str | None
    value_type: str
    note: str | None
    updated_at: datetime


@dataclass(frozen=True)
class TrendPointDTO:
    """A single historical data point in a metric trend."""

    metric_value: Decimal
    recorded_at: datetime


@dataclass(frozen=True)
class CustomerMetricTrendDTO:
    """Time-series trend data for a specific customer metric."""

    customer_id: UUID
    metric_definition_id: UUID
    metric_name: str
    display_name: str
    unit: str | None
    data_points: list[TrendPointDTO] = field(default_factory=list)
