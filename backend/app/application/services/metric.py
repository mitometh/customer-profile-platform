"""Metric query service for the metrics engine context."""

from datetime import datetime
from uuid import UUID

from app.application.dtos.metric import (
    CatalogEntryDTO,
    CustomerMetricDTO,
    CustomerMetricTrendDTO,
    TrendPointDTO,
)
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.infrastructure.models.metric import MetricDefinitionModel
from app.infrastructure.repositories.customer import SqlAlchemyCustomerRepository
from app.infrastructure.repositories.metric import (
    SqlAlchemyCustomerMetricHistoryRepository,
    SqlAlchemyCustomerMetricRepository,
    SqlAlchemyMetricDefinitionRepository,
)


class MetricQueryService:
    """Use-case orchestration for metric catalog, customer metrics, and trends."""

    def __init__(
        self,
        definition_repo: SqlAlchemyMetricDefinitionRepository,
        metric_repo: SqlAlchemyCustomerMetricRepository,
        history_repo: SqlAlchemyCustomerMetricHistoryRepository,
        customer_repo: SqlAlchemyCustomerRepository | None = None,
    ) -> None:
        self._definition_repo = definition_repo
        self._metric_repo = metric_repo
        self._history_repo = history_repo
        self._customer_repo = customer_repo

    async def get_catalog(self, permissions: list[str]) -> list[CatalogEntryDTO]:
        """Return the full metric definitions catalog.

        Gate 2: requires ``metrics.catalog.read`` permission.
        """
        if "metrics.catalog.read" not in permissions:
            raise ForbiddenError("metrics.catalog.read")

        definitions = await self._definition_repo.list_all()
        return [
            CatalogEntryDTO(
                id=d.id,
                name=d.name,
                display_name=d.display_name,
                description=d.description,
                unit=d.unit,
                value_type=d.value_type,
            )
            for d in definitions
        ]

    async def get_customer_metrics(self, customer_id: UUID, permissions: list[str]) -> list[CustomerMetricDTO]:
        """Return all pre-computed metric values for a customer.

        Gate 2: requires ``metrics.read`` permission.
        """
        if "metrics.read" not in permissions:
            raise ForbiddenError("metrics.read")

        if self._customer_repo is not None:
            customer = await self._customer_repo.get_by_id(customer_id)
            if customer is None:
                raise NotFoundError("Customer", customer_id)

        metrics = await self._metric_repo.get_for_customer(customer_id)
        return [
            CustomerMetricDTO(
                metric_definition_id=m.metric_definition_id,
                metric_name=m.metric_definition.name,
                display_name=m.metric_definition.display_name,
                metric_value=m.metric_value,
                unit=m.metric_definition.unit,
                description=m.metric_definition.description,
                value_type=m.metric_definition.value_type,
                note=m.note,
                updated_at=m.updated_at,
            )
            for m in metrics
        ]

    async def get_metric_history(
        self,
        customer_id: UUID,
        metric_id: UUID,
        since: datetime | None,
        until: datetime | None,
        limit: int,
        permissions: list[str],
    ) -> CustomerMetricTrendDTO:
        """Return historical trend data for a specific customer metric.

        Gate 2: requires ``metrics.read`` permission.

        Raises:
            NotFoundError: If the metric definition does not exist.
        """
        if "metrics.read" not in permissions:
            raise ForbiddenError("metrics.read")

        if self._customer_repo is not None:
            customer = await self._customer_repo.get_by_id(customer_id)
            if customer is None:
                raise NotFoundError("Customer", customer_id)

        definition = await self._definition_repo.get_by_id(metric_id)
        if definition is None:
            raise NotFoundError("MetricDefinition", metric_id)

        history = await self._history_repo.get_trend(
            customer_id=customer_id,
            metric_definition_id=metric_id,
            since=since,
            until=until,
            limit=limit,
        )

        data_points = [
            TrendPointDTO(
                metric_value=h.metric_value,
                recorded_at=h.recorded_at,
            )
            for h in history
        ]

        return CustomerMetricTrendDTO(
            customer_id=customer_id,
            metric_definition_id=metric_id,
            metric_name=definition.name,
            display_name=definition.display_name,
            unit=definition.unit,
            data_points=data_points,
        )

    # ------------------------------------------------------------------
    # Metric Definition Management (metrics.catalog.manage)
    # ------------------------------------------------------------------

    async def create_metric_definition(
        self,
        name: str,
        display_name: str,
        value_type: str,
        permissions: list[str],
        current_user_id: UUID,
        description: str | None = None,
        unit: str | None = None,
    ) -> CatalogEntryDTO:
        """Create a new metric definition.

        Gate 2: requires ``metrics.catalog.manage`` permission.

        Raises:
            ForbiddenError: If the caller lacks metrics.catalog.manage.
            ConflictError: If a metric with the same name already exists.
        """
        if "metrics.catalog.manage" not in permissions:
            raise ForbiddenError("metrics.catalog.manage")

        existing = await self._definition_repo.get_by_name(name)
        if existing is not None:
            raise ConflictError(f"Metric definition with name '{name}' already exists")

        model = MetricDefinitionModel(
            name=name,
            display_name=display_name,
            description=description,
            unit=unit,
            value_type=value_type,
            created_by=current_user_id,
            updated_by=current_user_id,
        )
        model = await self._definition_repo.create(model)

        return CatalogEntryDTO(
            id=model.id,
            name=model.name,
            display_name=model.display_name,
            description=model.description,
            unit=model.unit,
            value_type=model.value_type,
        )

    async def update_metric_definition(
        self,
        metric_id: UUID,
        updates: dict,
        permissions: list[str],
        current_user_id: UUID,
    ) -> CatalogEntryDTO:
        """Partially update a metric definition.

        Gate 2: requires ``metrics.catalog.manage`` permission.

        Raises:
            ForbiddenError: If the caller lacks metrics.catalog.manage.
            NotFoundError: If the metric definition does not exist or is soft-deleted.
        """
        if "metrics.catalog.manage" not in permissions:
            raise ForbiddenError("metrics.catalog.manage")

        definition = await self._definition_repo.get_by_id(metric_id)
        if definition is None:
            raise NotFoundError("MetricDefinition", metric_id)

        updatable_fields = ["display_name", "description", "unit", "value_type"]
        for field in updatable_fields:
            if field in updates and updates[field] is not None:
                setattr(definition, field, updates[field])

        definition.updated_by = current_user_id
        definition = await self._definition_repo.update(definition)

        return CatalogEntryDTO(
            id=definition.id,
            name=definition.name,
            display_name=definition.display_name,
            description=definition.description,
            unit=definition.unit,
            value_type=definition.value_type,
        )

    async def delete_metric_definition(
        self,
        metric_id: UUID,
        permissions: list[str],
        current_user_id: UUID,
    ) -> None:
        """Soft-delete a metric definition.

        Gate 2: requires ``metrics.catalog.manage`` permission.

        Raises:
            ForbiddenError: If the caller lacks metrics.catalog.manage.
            NotFoundError: If the metric definition does not exist or is already soft-deleted.
        """
        if "metrics.catalog.manage" not in permissions:
            raise ForbiddenError("metrics.catalog.manage")

        definition = await self._definition_repo.get_by_id(metric_id)
        if definition is None:
            raise NotFoundError("MetricDefinition", metric_id)

        await self._definition_repo.soft_delete(metric_id, deleted_by=current_user_id)
