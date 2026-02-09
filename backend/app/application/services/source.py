"""Source management service for the source integration context."""

import hashlib
import secrets
from uuid import UUID

from app.application.dtos.source import (
    SourceCreateResultDTO,
    SourceDetailDTO,
    SourceSummaryDTO,
)
from app.core.context import CallerContext
from app.core.exceptions import ConflictError, NotFoundError
from app.core.protocols import SourceRepository, TokenCache
from app.core.types import PaginatedResult, Pagination
from app.infrastructure.models.source import SourceModel


class SourceService:
    """CRUD operations for source management. Gate 2 permission checks at top of every method."""

    def __init__(
        self,
        source_repo: SourceRepository,
        token_cache: TokenCache,
    ) -> None:
        self._source_repo = source_repo
        self._token_cache = token_cache

    async def list_sources(
        self,
        pagination: Pagination,
        ctx: CallerContext,
    ) -> PaginatedResult[SourceSummaryDTO]:
        """Return a paginated list of sources.

        Gate 2: requires 'sources.read' permission.
        """
        ctx.require_permission("sources.read")

        result = await self._source_repo.list(pagination)

        dto_data = [self._to_summary_dto(src) for src in result.data]

        return PaginatedResult(
            data=dto_data,
            total=result.total,
            has_next=result.has_next,
            next_cursor=result.next_cursor,
        )

    async def get_source(
        self,
        source_id: UUID,
        ctx: CallerContext,
    ) -> SourceDetailDTO:
        """Get a single source by ID.

        Gate 2: requires 'sources.read' permission.

        Raises:
            ForbiddenError: If the caller lacks sources.read.
            NotFoundError: If the source does not exist.
        """
        ctx.require_permission("sources.read")

        source = await self._source_repo.get_by_id(source_id)
        if source is None:
            raise NotFoundError("Source", source_id)

        return self._to_detail_dto(source)

    async def create_source(
        self,
        name: str,
        description: str | None,
        ctx: CallerContext,
    ) -> SourceCreateResultDTO:
        """Create a new source with a generated API token.

        Gate 2: requires 'sources.manage' permission.

        The raw API token is returned only in this response. It is hashed
        with SHA256 before storage and never revealed again.

        Raises:
            ForbiddenError: If the caller lacks sources.manage.
            ConflictError: If the source name already exists.
        """
        ctx.require_permission("sources.manage")

        # Check name uniqueness
        existing = await self._source_repo.get_by_name(name)
        if existing is not None:
            raise ConflictError(f"Source with name '{name}' already exists")

        # Generate token
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

        source = SourceModel(
            name=name,
            description=description,
            api_token_hash=token_hash,
            is_active=True,
            created_by=ctx.user_id,
        )
        source = await self._source_repo.create(source)

        return SourceCreateResultDTO(
            id=source.id,
            name=source.name,
            api_token=raw_token,
            is_active=source.is_active,
            created_at=source.created_at,
        )

    async def update_source(
        self,
        source_id: UUID,
        updates: dict,
        ctx: CallerContext,
    ) -> SourceSummaryDTO:
        """Partially update a source (name, description, is_active).

        Gate 2: requires 'sources.manage' permission.

        Invalidates the Redis token cache if is_active changes.

        Raises:
            ForbiddenError: If the caller lacks sources.manage.
            NotFoundError: If the source does not exist.
            ConflictError: If the new name conflicts with another source.
        """
        ctx.require_permission("sources.manage")

        source = await self._source_repo.get_by_id(source_id)
        if source is None:
            raise NotFoundError("Source", source_id)

        if "name" in updates and updates["name"] is not None:
            # Check uniqueness if name is changing
            if updates["name"] != source.name:
                existing = await self._source_repo.get_by_name(updates["name"])
                if existing is not None:
                    raise ConflictError(f"Source with name '{updates['name']}' already exists")
            source.name = updates["name"]

        if "description" in updates:
            source.description = updates["description"]

        if "is_active" in updates and updates["is_active"] is not None:
            old_active = source.is_active
            source.is_active = updates["is_active"]
            # Invalidate cache if active status changed
            if old_active != source.is_active:
                await self._token_cache.invalidate_token(source.api_token_hash)

        source.updated_by = ctx.user_id
        source = await self._source_repo.update(source)

        return self._to_summary_dto(source)

    async def delete_source(
        self,
        source_id: UUID,
        ctx: CallerContext,
    ) -> None:
        """Soft-delete a source.

        Gate 2: requires 'sources.manage' permission.

        Invalidates the Redis token cache for the source.

        Raises:
            ForbiddenError: If the caller lacks sources.manage.
            NotFoundError: If the source does not exist.
        """
        ctx.require_permission("sources.manage")

        source = await self._source_repo.get_by_id(source_id)
        if source is None:
            raise NotFoundError("Source", source_id)

        # Invalidate cache before deleting
        await self._token_cache.invalidate_token(source.api_token_hash)

        await self._source_repo.soft_delete(source_id, deleted_by=ctx.user_id)

    async def get_active_sources(
        self,
        ctx: CallerContext,
    ) -> list[SourceSummaryDTO]:
        """Return all active (non-deleted) sources. Used by agent tools.

        Gate 2: requires 'sources.read' permission.
        """
        ctx.require_permission("sources.read")

        result = await self._source_repo.list(Pagination(limit=100))
        return [self._to_summary_dto(src) for src in result.data if src.is_active]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_summary_dto(source: SourceModel) -> SourceSummaryDTO:
        return SourceSummaryDTO(
            id=source.id,
            name=source.name,
            description=source.description,
            is_active=source.is_active,
            created_at=source.created_at,
        )

    @staticmethod
    def _to_detail_dto(source: SourceModel) -> SourceDetailDTO:
        return SourceDetailDTO(
            id=source.id,
            name=source.name,
            description=source.description,
            is_active=source.is_active,
            created_at=source.created_at,
            updated_at=source.updated_at,
        )
