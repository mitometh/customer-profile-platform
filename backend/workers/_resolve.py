"""Shared customer resolution utility for all workers.

Resolves a customer identifier to a UUID by matching against
company_name (case-insensitive) first, then email. Both lookups
respect soft-delete filtering (deleted_at IS NULL).
"""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models.customer import CustomerModel


async def resolve_customer(session: AsyncSession, identifier: str) -> UUID | None:
    """Resolve a customer identifier to a UUID.

    Lookup order:
        1. Case-insensitive company_name match.
        2. Case-insensitive email match.

    Returns:
        The customer's UUID if found, else None.
    """
    if not identifier:
        return None

    # Try company_name first
    result = await session.execute(
        select(CustomerModel).where(
            func.lower(CustomerModel.company_name) == func.lower(identifier),
            CustomerModel.deleted_at.is_(None),
        )
    )
    customer = result.scalar_one_or_none()
    if customer:
        return customer.id

    # Try email
    result = await session.execute(
        select(CustomerModel).where(
            func.lower(CustomerModel.email) == func.lower(identifier),
            CustomerModel.deleted_at.is_(None),
        )
    )
    customer = result.scalar_one_or_none()
    return customer.id if customer else None
