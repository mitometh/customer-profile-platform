"""Customer routes for customer management context."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response

from app.api.dependencies import require_permission
from app.api.schemas.common import PaginatedResponse, PaginationMeta
from app.api.schemas.customer import (
    CustomerCreateRequest,
    CustomerDetailSchema,
    CustomerSummarySchema,
    CustomerUpdateRequest,
)
from app.api.service_factories import get_customer_service
from app.application.services.customer import CustomerService
from app.core.context import CallerContext
from app.core.types import Pagination

router = APIRouter()


def _dto_to_detail_schema(dto) -> CustomerDetailSchema:
    """Map a CustomerDetailDTO to a CustomerDetailSchema."""
    return CustomerDetailSchema(
        id=dto.id,
        company_name=dto.company_name,
        contact_name=dto.contact_name,
        email=dto.email,
        phone=dto.phone,
        industry=dto.industry,
        contract_value=dto.contract_value,
        currency_code=dto.currency_code,
        signup_date=dto.signup_date,
        source_name=dto.source_name,
        notes=dto.notes,
        created_at=dto.created_at,
        updated_at=dto.updated_at,
        recent_events=[
            {
                "id": e.id,
                "customer_id": e.customer_id,
                "event_type": e.event_type,
                "title": e.title,
                "description": e.description,
                "occurred_at": e.occurred_at,
                "source_name": e.source_name,
                "data": e.data,
            }
            for e in dto.recent_events
        ],
        metrics=dto.metrics,
    )


@router.get("", response_model=PaginatedResponse[CustomerSummarySchema])
async def list_customers(
    search: str | None = Query(None, description="Company name search (case-insensitive)"),
    cursor: str | None = Query(None, description="Pagination cursor"),
    limit: int = Query(20, ge=1, le=100, description="Page size"),
    ctx: CallerContext = Depends(require_permission("customers.read")),
    service: CustomerService = Depends(get_customer_service),
) -> PaginatedResponse[CustomerSummarySchema]:
    """List customers with optional search and cursor-based pagination."""
    result = await service.list_customers(
        search=search,
        pagination=Pagination(cursor=cursor, limit=limit),
        ctx=ctx,
    )
    return PaginatedResponse(
        data=[CustomerSummarySchema(**dto.__dict__) for dto in result.data],
        pagination=PaginationMeta(
            total=result.total,
            limit=limit,
            has_next=result.has_next,
            next_cursor=result.next_cursor,
        ),
    )


@router.get("/{customer_id}", response_model=CustomerDetailSchema)
async def get_customer(
    customer_id: UUID,
    ctx: CallerContext = Depends(require_permission("customers.read")),
    service: CustomerService = Depends(get_customer_service),
) -> CustomerDetailSchema:
    """Get full customer 360 profile with recent events and metrics."""
    dto = await service.get_customer_detail(customer_id, ctx=ctx)
    return _dto_to_detail_schema(dto)


@router.post("", response_model=CustomerDetailSchema, status_code=201)
async def create_customer(
    body: CustomerCreateRequest,
    ctx: CallerContext = Depends(require_permission("customers.manage")),
    service: CustomerService = Depends(get_customer_service),
) -> CustomerDetailSchema:
    """Create a new customer (admin only)."""
    dto = await service.create_customer(
        company_name=body.company_name,
        contact_name=body.contact_name,
        email=body.email,
        phone=body.phone,
        industry=body.industry,
        contract_value=body.contract_value,
        currency_code=body.currency_code,
        signup_date=body.signup_date,
        notes=body.notes,
        ctx=ctx,
    )
    return _dto_to_detail_schema(dto)


@router.patch("/{customer_id}", response_model=CustomerDetailSchema)
async def update_customer(
    customer_id: UUID,
    body: CustomerUpdateRequest,
    ctx: CallerContext = Depends(require_permission("customers.manage")),
    service: CustomerService = Depends(get_customer_service),
) -> CustomerDetailSchema:
    """Update a customer (admin only)."""
    updates = body.model_dump(exclude_unset=True)
    dto = await service.update_customer(
        customer_id=customer_id,
        updates=updates,
        ctx=ctx,
    )
    return _dto_to_detail_schema(dto)


@router.delete("/{customer_id}", status_code=204)
async def delete_customer(
    customer_id: UUID,
    ctx: CallerContext = Depends(require_permission("customers.manage")),
    service: CustomerService = Depends(get_customer_service),
) -> Response:
    """Soft-delete a customer (admin only)."""
    await service.delete_customer(
        customer_id=customer_id,
        ctx=ctx,
    )
    return Response(status_code=204)
