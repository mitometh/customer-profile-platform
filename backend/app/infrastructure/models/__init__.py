"""SQLAlchemy model registry.

All models are imported here for Alembic auto-discovery via
``target_metadata = Base.metadata``.
"""

from app.infrastructure.models.base import Base
from app.infrastructure.models.chat import ChatMessageModel, ChatSessionModel
from app.infrastructure.models.customer import CustomerModel
from app.infrastructure.models.event import EventModel
from app.infrastructure.models.metric import (
    CustomerMetricHistoryModel,
    CustomerMetricModel,
    MetricDefinitionModel,
)
from app.infrastructure.models.role import PermissionModel, RoleModel, RolePermissionModel
from app.infrastructure.models.source import SourceModel
from app.infrastructure.models.user import UserModel

__all__ = [
    "Base",
    "ChatMessageModel",
    "ChatSessionModel",
    "CustomerMetricHistoryModel",
    "CustomerMetricModel",
    "CustomerModel",
    "EventModel",
    "MetricDefinitionModel",
    "PermissionModel",
    "RoleModel",
    "RolePermissionModel",
    "SourceModel",
    "UserModel",
]
