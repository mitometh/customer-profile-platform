"""Pydantic schemas for metric endpoints."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MetricValueType(str, Enum):
    """Allowed metric value types."""

    integer = "integer"
    decimal = "decimal"
    percentage = "percentage"


class MetricDefinitionCreateRequest(BaseModel):
    """POST /api/metrics/catalog request body."""

    name: str = Field(..., max_length=100)
    display_name: str = Field(..., max_length=255)
    description: str | None = None
    unit: str | None = Field(None, max_length=50)
    value_type: MetricValueType


class MetricDefinitionUpdateRequest(BaseModel):
    """PATCH /api/metrics/catalog/{id} request body."""

    display_name: str | None = Field(None, max_length=255)
    description: str | None = None
    unit: str | None = Field(None, max_length=50)
    value_type: MetricValueType | None = None


class MetricCatalogEntrySchema(BaseModel):
    """Single metric definition in the catalog."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    display_name: str
    description: str | None = None
    unit: str | None = None
    value_type: str


class MetricCatalogResponse(BaseModel):
    """GET /api/metrics/catalog response body."""

    metrics: list[MetricCatalogEntrySchema]


class CustomerMetricValueSchema(BaseModel):
    """Single metric value for a customer, enriched with definition info."""

    model_config = ConfigDict(from_attributes=True)

    metric_definition_id: UUID
    metric_name: str
    display_name: str
    metric_value: Decimal
    unit: str | None = None
    description: str | None = None
    value_type: str
    note: str | None = None
    updated_at: datetime


class CustomerMetricsResponse(BaseModel):
    """GET /api/customers/{customer_id}/metrics response body."""

    customer_id: UUID
    metrics: list[CustomerMetricValueSchema]


class TrendPointSchema(BaseModel):
    """Single data point in a metric trend time series."""

    model_config = ConfigDict(from_attributes=True)

    metric_value: Decimal
    recorded_at: datetime


class CustomerMetricTrendSchema(BaseModel):
    """GET /api/customers/{customer_id}/metrics/{metric_id}/history response body."""

    model_config = ConfigDict(from_attributes=True)

    customer_id: UUID
    metric_definition_id: UUID
    metric_name: str
    display_name: str
    unit: str | None = None
    data_points: list[TrendPointSchema]
