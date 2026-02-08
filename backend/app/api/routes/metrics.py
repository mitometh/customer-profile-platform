"""Metric routes for catalog, customer metrics, and trend history.

Two routers are exported:
- ``catalog_router``: mounted at ``/api/metrics`` for the catalog endpoint
  and metric definition management (POST, PATCH, DELETE).
- ``customer_metrics_router``: mounted at ``/api/customers/{customer_id}/metrics``
  for per-customer metric values and trend history.
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import CurrentUserDTO, get_db, require_permission
from app.api.schemas.metric import (
    CustomerMetricsResponse,
    CustomerMetricTrendSchema,
    CustomerMetricValueSchema,
    MetricCatalogEntrySchema,
    MetricCatalogResponse,
    MetricDefinitionCreateRequest,
    MetricDefinitionUpdateRequest,
    TrendPointSchema,
)
from app.application.services.metric import MetricQueryService
from app.infrastructure.repositories.customer import SqlAlchemyCustomerRepository
from app.infrastructure.repositories.metric import (
    SqlAlchemyCustomerMetricHistoryRepository,
    SqlAlchemyCustomerMetricRepository,
    SqlAlchemyMetricDefinitionRepository,
)

catalog_router = APIRouter()
customer_metrics_router = APIRouter()


def _build_metric_service(db: AsyncSession) -> MetricQueryService:
    """Wire up the MetricQueryService with its repositories."""
    return MetricQueryService(
        definition_repo=SqlAlchemyMetricDefinitionRepository(db),
        metric_repo=SqlAlchemyCustomerMetricRepository(db),
        history_repo=SqlAlchemyCustomerMetricHistoryRepository(db),
        customer_repo=SqlAlchemyCustomerRepository(db),
    )


# ---------------------------------------------------------------------------
# Catalog: GET /api/metrics/catalog
# ---------------------------------------------------------------------------


@catalog_router.get("/catalog", response_model=MetricCatalogResponse)
async def get_metric_catalog(
    user: CurrentUserDTO = Depends(require_permission("metrics.catalog.read")),
    db: AsyncSession = Depends(get_db),
) -> MetricCatalogResponse:
    """Return the full metric definitions catalog (no pagination)."""
    service = _build_metric_service(db)
    entries = await service.get_catalog(user.permissions)
    return MetricCatalogResponse(
        metrics=[
            MetricCatalogEntrySchema(
                id=e.id,
                name=e.name,
                display_name=e.display_name,
                description=e.description,
                unit=e.unit,
                value_type=e.value_type,
            )
            for e in entries
        ],
    )


# ---------------------------------------------------------------------------
# Catalog management: POST / PATCH / DELETE /api/metrics/catalog
# ---------------------------------------------------------------------------


@catalog_router.post("/catalog", response_model=MetricCatalogEntrySchema, status_code=201)
async def create_metric_definition(
    body: MetricDefinitionCreateRequest,
    user: CurrentUserDTO = Depends(require_permission("metrics.catalog.manage")),
    db: AsyncSession = Depends(get_db),
) -> MetricCatalogEntrySchema:
    """Create a new metric definition (admin only)."""
    service = _build_metric_service(db)
    dto = await service.create_metric_definition(
        name=body.name,
        display_name=body.display_name,
        description=body.description,
        unit=body.unit,
        value_type=body.value_type.value,
        permissions=user.permissions,
        current_user_id=user.id,
    )
    return MetricCatalogEntrySchema(
        id=dto.id,
        name=dto.name,
        display_name=dto.display_name,
        description=dto.description,
        unit=dto.unit,
        value_type=dto.value_type,
    )


@catalog_router.patch("/catalog/{metric_id}", response_model=MetricCatalogEntrySchema)
async def update_metric_definition(
    metric_id: UUID,
    body: MetricDefinitionUpdateRequest,
    user: CurrentUserDTO = Depends(require_permission("metrics.catalog.manage")),
    db: AsyncSession = Depends(get_db),
) -> MetricCatalogEntrySchema:
    """Update a metric definition (admin only)."""
    service = _build_metric_service(db)
    updates = body.model_dump(exclude_unset=True)
    # Convert enum to string value if present
    if "value_type" in updates and updates["value_type"] is not None:
        updates["value_type"] = updates["value_type"].value
    dto = await service.update_metric_definition(
        metric_id=metric_id,
        updates=updates,
        permissions=user.permissions,
        current_user_id=user.id,
    )
    return MetricCatalogEntrySchema(
        id=dto.id,
        name=dto.name,
        display_name=dto.display_name,
        description=dto.description,
        unit=dto.unit,
        value_type=dto.value_type,
    )


@catalog_router.delete("/catalog/{metric_id}", status_code=204)
async def delete_metric_definition(
    metric_id: UUID,
    user: CurrentUserDTO = Depends(require_permission("metrics.catalog.manage")),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Soft-delete a metric definition (admin only)."""
    service = _build_metric_service(db)
    await service.delete_metric_definition(
        metric_id=metric_id,
        permissions=user.permissions,
        current_user_id=user.id,
    )
    return Response(status_code=204)


# ---------------------------------------------------------------------------
# Customer metrics: GET /api/customers/{customer_id}/metrics
# ---------------------------------------------------------------------------


@customer_metrics_router.get("", response_model=CustomerMetricsResponse)
async def get_customer_metrics(
    customer_id: UUID,
    user: CurrentUserDTO = Depends(require_permission("metrics.read")),
    db: AsyncSession = Depends(get_db),
) -> CustomerMetricsResponse:
    """Return all pre-computed metric values for a customer."""
    service = _build_metric_service(db)
    metrics = await service.get_customer_metrics(customer_id, user.permissions)
    return CustomerMetricsResponse(
        customer_id=customer_id,
        metrics=[
            CustomerMetricValueSchema(
                metric_id=m.metric_id,
                metric_name=m.metric_name,
                display_name=m.display_name,
                value=m.value,
                unit=m.unit,
                description=m.description,
                value_type=m.value_type,
                note=m.note,
                updated_at=m.updated_at,
            )
            for m in metrics
        ],
    )


# ---------------------------------------------------------------------------
# Trend history: GET /api/customers/{customer_id}/metrics/{metric_id}/history
# ---------------------------------------------------------------------------


@customer_metrics_router.get(
    "/{metric_id}/history",
    response_model=CustomerMetricTrendSchema,
)
async def get_customer_metric_history(
    customer_id: UUID,
    metric_id: UUID,
    since: datetime | None = Query(default=None),
    until: datetime | None = Query(default=None),
    limit: int = Query(default=90, ge=1, le=365),
    user: CurrentUserDTO = Depends(require_permission("metrics.read")),
    db: AsyncSession = Depends(get_db),
) -> CustomerMetricTrendSchema:
    """Return historical trend data for a specific customer metric."""
    service = _build_metric_service(db)
    trend = await service.get_metric_history(
        customer_id=customer_id,
        metric_id=metric_id,
        since=since,
        until=until,
        limit=limit,
        permissions=user.permissions,
    )
    return CustomerMetricTrendSchema(
        customer_id=trend.customer_id,
        metric_id=trend.metric_id,
        metric_name=trend.metric_name,
        display_name=trend.display_name,
        unit=trend.unit,
        data_points=[TrendPointSchema(metric_value=dp.value, recorded_at=dp.recorded_at) for dp in trend.data_points],
    )
