"""Metric repositories for the metrics engine context."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.models.metric import (
    CustomerMetricHistoryModel,
    CustomerMetricModel,
    MetricDefinitionModel,
)
from app.infrastructure.repositories.base import BaseRepository


class SqlAlchemyMetricDefinitionRepository(BaseRepository[MetricDefinitionModel]):
    """Data-access layer for metric definitions (catalog)."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, MetricDefinitionModel)

    async def list_all(self) -> list[MetricDefinitionModel]:
        """Return all non-deleted metric definitions (no pagination — small dataset)."""
        stmt = select(MetricDefinitionModel)
        stmt = self._apply_soft_delete_filter(stmt)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_name(self, name: str) -> MetricDefinitionModel | None:
        """Fetch a metric definition by its unique name, excluding soft-deleted rows."""
        stmt = select(MetricDefinitionModel).where(
            MetricDefinitionModel.name == name,
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()


class SqlAlchemyCustomerMetricRepository(BaseRepository[CustomerMetricModel]):
    """Data-access layer for current customer metric values."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, CustomerMetricModel)

    async def get_for_customer(self, customer_id: UUID) -> list[CustomerMetricModel]:
        """Return all non-deleted metrics for a customer with eager-loaded definitions."""
        stmt = (
            select(CustomerMetricModel)
            .where(CustomerMetricModel.customer_id == customer_id)
            .options(selectinload(CustomerMetricModel.metric_definition))
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def upsert(
        self,
        customer_id: UUID,
        metric_definition_id: UUID,
        value: Decimal,
        note: str | None = None,
    ) -> CustomerMetricModel:
        """Insert or update a customer metric value.

        If a record for (customer_id, metric_definition_id) already exists,
        update its value and note. Otherwise, create a new record.
        """
        stmt = select(CustomerMetricModel).where(
            CustomerMetricModel.customer_id == customer_id,
            CustomerMetricModel.metric_definition_id == metric_definition_id,
        )
        stmt = self._apply_soft_delete_filter(stmt)
        result = await self._session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing is not None:
            existing.metric_value = value
            existing.note = note
            await self._session.flush()
            await self._session.refresh(existing)
            return existing

        new_metric = CustomerMetricModel(
            customer_id=customer_id,
            metric_definition_id=metric_definition_id,
            metric_value=value,
            note=note,
        )
        self._session.add(new_metric)
        await self._session.flush()
        await self._session.refresh(new_metric)
        return new_metric


class SqlAlchemyCustomerMetricHistoryRepository:
    """Data-access layer for append-only metric history snapshots."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def append(
        self,
        customer_id: UUID,
        metric_definition_id: UUID,
        value: Decimal,
    ) -> None:
        """Create a new historical snapshot record (append-only)."""
        record = CustomerMetricHistoryModel(
            customer_id=customer_id,
            metric_definition_id=metric_definition_id,
            metric_value=value,
        )
        self._session.add(record)
        await self._session.flush()

    async def get_trend(
        self,
        customer_id: UUID,
        metric_definition_id: UUID,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int = 90,
    ) -> list[CustomerMetricHistoryModel]:
        """Return historical data points for a customer metric.

        Args:
            customer_id: The customer's UUID.
            metric_definition_id: The metric definition's UUID.
            since: Optional lower bound on recorded_at (inclusive).
            until: Optional upper bound on recorded_at (inclusive).
            limit: Maximum number of data points to return (default 90).

        Returns:
            List of history records ordered by recorded_at DESC.
        """
        stmt = select(CustomerMetricHistoryModel).where(
            CustomerMetricHistoryModel.customer_id == customer_id,
            CustomerMetricHistoryModel.metric_definition_id == metric_definition_id,
        )

        if since is not None:
            stmt = stmt.where(CustomerMetricHistoryModel.recorded_at >= since)
        if until is not None:
            stmt = stmt.where(CustomerMetricHistoryModel.recorded_at <= until)

        stmt = stmt.order_by(CustomerMetricHistoryModel.recorded_at.desc())
        stmt = stmt.limit(limit)

        result = await self._session.execute(stmt)
        return list(result.scalars().all())
